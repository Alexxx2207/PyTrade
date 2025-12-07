import { BrowserRouter, Route, Routes } from "react-router-dom"
import { ChartsPage } from "../pages/charts"

export function App() {
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
