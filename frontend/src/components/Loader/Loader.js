import styles from "./loader.module.css";

export default function Loader() {
  return (
    <div className={styles.loaderContainer}>
      <div className={styles.loader}>
        <div
          className={`justify-content-center ${styles["jimu-primary-loading"]}`}
        ></div>
      </div>
    </div>
  );
}
