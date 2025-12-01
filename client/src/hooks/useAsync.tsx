import { useEffect } from "react"
import { useAsyncAction } from "./useAsyncAction"

export function useAsync<Args extends [], Result>(
    action: (...args: Args) => Promise<Result>,
    dependencyList: [],
) {
    const { data, loading, error, trigger } = useAsyncAction(action, { initiallyLoading: true })

    useEffect(
        (...args: Args) => {
            trigger(...args) 
        },
        dependencyList
    )

    return { data, loading, error, reload: trigger }
}
