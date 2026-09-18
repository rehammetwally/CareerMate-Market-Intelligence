@router.get("/split_comparison")
async def get_split_comparison_data():
    """Get chart data for both old and new CSVs for split-screen comparison"""
    try:
        # Load old data
        if not CSV_FILE_PATH.exists():
            return JSONResponse(status_code=404, content={"success": False, "error": "Original data not found"})
        
        # Load new data
        if not NEW_CSV_FILE_PATH.exists():
            return JSONResponse(status_code=404, content={"success": False, "error": "New data not found. Please generate it first."})
        
        # Function to process dataframe into chart data
        def process_chart_data(df, df_name):
            # Ensure numeric columns
            cols_to_convert = ['Global_Job_Demand', 'Egypt_Job_Demand', 'Freelancing_Opportunities',
                             'Linkedin_Distribution', 'Ziprecruiter_Distribution', 'Upwork_Distribution',
                             'Khamsat_Distribution',  'Mostakel_Distribution', 'Freelancer_Distribution',
                             'Indeed_Distribution', 'Market_Attractiveness_Rating', 'AI_Skills_Count']
            
            for col in cols_to_convert:
                if col in df.columns:
                    logger.info(f"Converting column '{col}' to numeric...")
                    df[col] = df[col].apply(clean_numeric_value)
            
            # Top 10 Jobs
            top_jobs = []
            if len(df) > 0:
                top_jobs_df = df.nlargest(10, 'Global_Job_Demand')[['Title', 'Track', 'Global_Job_Demand', 'Egypt_Job_Demand', 'Market_Attractiveness_Rating']].copy()
                for _, row in top_jobs_df.iterrows():
                    top_jobs.append({
                        'job_title': str(row['Title']),
                        'track': str(row['Track']),
                        'global_demand': int(row['Global_Job_Demand']),
                        'egypt_demand': int(row['Egypt_Job_Demand']),
                        'rating': float(row['Market_Attractiveness_Rating'])
                    })
            
            # Track Analysis
            track_analysis = []
            if 'Track' in df.columns:
                tracks = df.groupby('Track').agg({
                    'Global_Job_Demand': 'sum',
                    'Egypt_Job_Demand': 'sum'
                }).reset_index()
                
                for _, row in tracks.iterrows():
                    track_analysis.append({
                        'track': str(row['Track']),
                        'global_demand': int(row['Global_Job_Demand']),
                        'egypt_demand': int(row['Egypt_Job_Demand'])
                    })
            
            # Top Skills
            all_skills = {}
            for _, row in df.iterrows():
                skills = extract_skills_list(row.get('AI_Extracted_Skills', ''), row.get('AI_Skills_Count', 0))
                demand = row['Global_Job_Demand']
                for skill in skills:
                    if skill and skill.strip():
                        skill = skill.strip()
                        all_skills[skill] = all_skills.get(skill, 0) + demand
            
            top_skills = [
                {'skill_name': skill, 'total_demand': int(demand)}
                for skill, demand in sorted(all_skills.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            
            # Statistics
            statistics = {
                'total_jobs': len(df),
                'total_global_demand': int(df['Global_Job_Demand'].sum()),
                'total_egypt_demand': int(df['Egypt_Job_Demand'].sum()),
                'avg_rating': float(df['Market_Attractiveness_Rating'].mean())
            }
            
            return {
                'name': df_name,
                'top_jobs': top_jobs,
                'track_analysis': track_analysis,
                'top_skills': top_skills,
                'statistics': statistics
            }
        
        # Load and process old data
        df_old = pd.read_csv(CSV_FILE_PATH)
        old_chart_data = process_chart_data(df_old.copy(), "Original Data")
        
        # Load and process new data
        df_new = pd.read_csv(NEW_CSV_FILE_PATH, on_bad_lines='skip')
        df_new.columns = df_new.columns.str.strip().str.replace('_', ' ').str.title().str.replace(' ', '_')
        new_chart_data = process_chart_data(df_new.copy(), "New Generated Data")
        
        return {
            "success": True,
            "old_data": old_chart_data,
            "new_data": new_chart_data
        }
        
    except Exception as e:
        logger.error(f"Split comparison failed: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

