import { config } from "../config"

interface RequestData {
    headers?: Record<string, unknown>
    queryParams?: Record<string, string | number | boolean>
    body?: Record<string, unknown>
}

class ApiService {
    async get<T>(path: string, data?: RequestData) {
        return request<T>("GET", path, data)
    }

    async post<T>(path: string, data?: RequestData) {
        return request<T>("POST", path, data)
    }

    async put<T>(path: string, data?: RequestData) {
        return request<T>("PUT", path, data)
    }

    async patch<T>(path: string, data?: RequestData) {
        return request<T>("PATCH", path, data)
    }

    async delete<T>(path: string, data?: RequestData) {
        return request<T>("DELETE", path, data)
    }
}

async function request<T>(
    method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE",
    path: string,
    data?: RequestData,
) {
    const url = new URL(
        config.backendAddress.replace(/^\/+|\/+$/g, "") + "/" + path.replace(/^\/+|\/+$/g, ""),
    )

    if (data?.queryParams) {
        Object.entries(data.queryParams).forEach(([key, value]) => {
            if (Array.isArray(value)) {
                value.forEach((v) => url.searchParams.append(key, String(v)))
            } else {
                url.searchParams.set(key, String(value))
            }
        })
    }

    const response = await fetch(url, {
        method: method,
        headers: {
            "Content-Type": "application/json",
            ...(data?.headers ?? {}),
        },
        ...(data?.body ? { body: JSON.stringify(data.body) } : undefined),
    })

    if (!response.ok) {
        throw new Error("Unsuccessful response")
    }

    return await response.json() as T

}

export const api = new ApiService()
