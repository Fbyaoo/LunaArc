import {defineStore} from 'pinia'


export type SessionState =
'idle'
|'shuffling'
|'selecting'
|'card_selected'
|'reading'
|'completed'
|'error'


export const useReadingStore =
defineStore('reading',{


state:()=>({

state:'idle' as SessionState,

question:'',

})


,

actions:{


changeState(
newState:SessionState
){

this.state=newState

}


}


})