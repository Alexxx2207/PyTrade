import { useAsync } from "../hooks/useAsync"
import { instrumentService } from "../services/instruments-service"

export function App() {
    const { data, loading, error } = useAsync(
      async () => await instrumentService.getData("ES"),
      []
    )

    if (loading || error || !data) {
        return null
    }

    return (
      <p>{data.instrument}</p>
    )
}
