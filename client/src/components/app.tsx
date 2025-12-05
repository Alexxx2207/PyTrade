import { BrowserRouter, Route, Routes } from "react-router-dom"
import { useAsync } from "../hooks/useAsync"
import { instrumentService } from "../services/instruments-service"
import { ChartsPage } from "../pages/charts"

export function App() {
    const { data, loading, error } = useAsync(
      async () => await instrumentService.getData("ES"),
      []
    )

    if (loading || error || !data) {
        return null
    }

    return (
      <Routing />
    )
}

function Routing() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ChartsPage/>}/>
      </Routes>
    </BrowserRouter>
  )
}
