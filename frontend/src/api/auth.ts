import { apiFetch } from './http'


export interface LoginRequest {

email:string

password:string

}



export interface RegisterRequest {

email:string

password:string

display_name:string

}



export interface AuthResponse {


access_token:string


token_type:string


user:{

id:number

email:string

display_name:string

plan:string

}


}



export function login(

data:LoginRequest

){

return apiFetch<AuthResponse>(

'/auth/login',

{

method:'POST',

body:JSON.stringify(data)

}

)

}



export function register(

data:RegisterRequest

){

return apiFetch<AuthResponse>(

'/auth/register',

{

method:'POST',

body:JSON.stringify(data)

}

)

}