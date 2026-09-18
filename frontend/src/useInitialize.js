import { useState, useEffect } from 'react';

export function useInitialize(url, onInitialize) {
  const [loading, setLoading] = useState(true);
  const [text, setText] = useState('');

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    fetch(url)
      .then(response => response.json())
      .then(data => {
        if (isMounted) {
          const initText = data.initialText || 'No initial text';
          setText(initText);
          if (onInitialize) onInitialize(initText);
          setLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) {
          setText('Error loading initial data');
          if (onInitialize) onInitialize('Error loading initial data');
          setLoading(false);
        }
      });

    return () => { isMounted = false; };
  }, [url, onInitialize]);

  return { loading, text };
}
