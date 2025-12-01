import { defaults } from "lodash"
import { useRef, useState } from "react"

interface State<T> {
    loading: boolean | undefined
    data: T | undefined
    error: unknown | undefined
}

interface Options {
    initiallyLoading: boolean
    persistData: boolean
}

const DEFAULT_OPTIONS: Partial<Options> = {
    initiallyLoading: false,
    persistData: true,
}

export function useAsyncAction<Args extends [], Result>(
    action: (...args: Args) => Promise<Result>,
    options?: Partial<Options>,
) {
    const optionsModified = defaults({}, options, DEFAULT_OPTIONS)

    const [state, setState] = useState<State<Result>>({
        loading: false,
        data: undefined,
        error: undefined,
    })

    const callCount = useRef(0)    

    const perform = async (...args: Args) => {
        setState((state) => ({
            loading: true,
            data: optionsModified.persistData ? state.data : undefined,
            error: undefined,
        }))

        callCount.current++
        const callId = callCount.current

        
        try {
            const result = await action(...args)

            if (callId === callCount.current) {
                setState({
                    loading: false,
                    data: result,
                    error: undefined,
                })
            }
        } catch (error) {
            setState({
                loading: false,
                data: undefined,
                error: error,
            })
        }
    }

    const trigger = (...args: Args) => {
        perform(...args).catch()
    }

    return { ...state, perform, trigger }
}
