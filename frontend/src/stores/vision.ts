import {defineStore} from 'pinia'


export const useVisionStore =
defineStore('vision',{

state:()=>({

gesture:null,

confidence:0

})


})