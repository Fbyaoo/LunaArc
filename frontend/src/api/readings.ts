import { apiFetch } from './http'


export interface DrawRequest {


question:string|null


spread_type:

'daily_card'
|
'single_card'
|
'three_card'


}



export interface DrawResponse {


cards:any[]


reading:{

status:string

summary:string

card_readings:any[]

synthesis:string

advice:string[]

reading_id:number

saved:boolean

created_at:string

}


}



export function drawAndRead(

data:DrawRequest

){


return apiFetch<DrawResponse>(

'/draw-and-read',

{

method:'POST',

body:
JSON.stringify(data)

}

)


}



export function getRecentReadings(

limit=3

){

return apiFetch(

`/readings/recent?limit=${limit}`

)

}



export function getHistory(){

return apiFetch(

'/history'

)

}



export function getReadingDetail(

id:number|string

){

return apiFetch(

`/readings/${id}`

)

}



export function saveReading(

id:number|string,

saved:boolean

){

return apiFetch(

`/readings/${id}`,

{

method:'PATCH',

body:

JSON.stringify({

saved

})

}

)

}

export function setReadingSaved(
  id:number|string,
  saved:boolean
){

  return saveReading(
    id,
    saved
  )

}