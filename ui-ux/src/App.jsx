import { createBrowserRouter, RouterProvider } from "react-router-dom";
import "./App.css";
import Home from "./components/Home";
import RootLayout from "./components/RootLayout";
import Login from "./components/Login";
const router = createBrowserRouter([
    {
        path: "/",
        element: <RootLayout />,
        children: [
            {
                index: true,
                element: <Login />,
            },
            { path: "home", element: <Home /> },
        ],
    },
]);
function App() {
    return <RouterProvider router={router} />;
}

export default App;
