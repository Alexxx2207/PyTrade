import z from "zod";

export const config = z.object({
    VITE_BACKEND_ADDRESS: z.string()
}).transform((obj) => ({
    backendAddress: obj.VITE_BACKEND_ADDRESS
})).parse(import.meta.env)
