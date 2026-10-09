import { useEffect, useState } from 'react';

/**
 * Runs an async fake-API function when the component mounts
 * and exposes { data, loading, error }.
 *
 * E.g.: const { data: patients, loading } = useFakeApi(getPatients);
 */
export function useFakeApi(fetcher) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true; // avoids updating state if the component unmounts before the response
    setLoading(true);
    fetcher()
      .then((result) => active && setData(result))
      .catch((e) => active && setError(e.message))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [fetcher]);

  return { data, loading, error };
}
