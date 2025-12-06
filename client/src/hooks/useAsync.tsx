import { useEffect, type DependencyList } from "react"
import { useAsyncAction } from "./useAsyncAction"

export function useAsync<Result>(
  action: () => Promise<Result>,
  dependencyList: DependencyList,
) {
  const { data, loading, error, trigger } = useAsyncAction(action, { initiallyLoading: true })

  useEffect(() => {
      trigger() 
    },
    dependencyList
  )

  return { data, loading, error, reload: trigger }
}
