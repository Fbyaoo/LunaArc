import ref from 'vue'
<template>

  <div class="auth-portal">


    <div class="auth-card">


      <div class="title">


        <h1>
          LUNAARC
        </h1>


        <h2>
          AI TAROT GUIDE
        </h2>


      </div>




      <div class="form">


        <input v-model="email" type="email" placeholder="Email" />



        <input v-model="password" type="password" placeholder="Password" />



<button
  type="button"
  class="login-button"
  :disabled="isSubmitting"
  @click="handleLogin"
>
  <span v-if="!isSubmitting">
    Log In / Sign Up
  </span>

  <span v-else>
    Entering LunaArc...
  </span>
</button>


      </div>





      <div class="divider">

        or continue with

      </div>




      <div class="social">


        <button class="social-btn">

          <Icon icon="logos:google-icon" />

        </button>



        <button class="social-btn">


          <Icon icon="logos:apple" />


        </button>


      </div>





      <p class="terms">


        By continuing, you agree to LunaArc Terms of Service and Privacy Policy.


      </p>



    </div>



  </div>

</template>




<script setup lang="ts">

import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { login, register } from '../../api/auth'


const router = useRouter()


const email = ref('')
const password = ref('')


const isSubmitting = ref(false)

const loginError = ref('')


const isRegisterMode = ref(false)



async function handleLogin(): Promise<void> {

  if (isSubmitting.value) {
    return
  }


  if (!email.value || !password.value) {

    loginError.value =
      'Please enter email and password.'

    return
  }



  isSubmitting.value = true

  loginError.value = ''



  try {


    let response



    if (isRegisterMode.value) {


      response = await register({

        email: email.value,

        password: password.value,

        display_name:
          email.value.split('@')[0]

      })


    } else {


      response = await login({

        email: email.value,

        password: password.value

      })


    }



    /*
      保存 Access Token
      后续所有 API 自动读取
    */

    localStorage.setItem(

      'access_token',

      response.access_token

    )



    /*
      保存用户信息
    */

    localStorage.setItem(

      'lunaarc_user',

      JSON.stringify(response.user)

    )



    await router.push('/home')



  } catch(error) {


    if(error instanceof Error){

      loginError.value =
        error.message

    }
    else{

      loginError.value =
        'Unable to enter LunaArc.'

    }


  } finally {


    isSubmitting.value = false


  }

}



function toggleRegister(){

  isRegisterMode.value =
    !isRegisterMode.value

  loginError.value = ''

}


</script>





<style scoped>
.auth-portal {


  position: absolute;


  inset: 0;


  display: flex;


  justify-content: flex-end;


  align-items: center;



  padding-right: 12%;


  z-index: 20;



  animation:

    fadeIn 1.2s ease forwards;


}




@keyframes fadeIn {


  from {


    opacity: 0;


    transform:

      translateY(30px);



  }



  to {


    opacity: 1;


    transform:

      translateY(0);



  }


}







.auth-card {


  position: relative;


  width: 370px;


  min-height: 520px;



  padding:

    45px 40px;



  background:

    rgba(255, 255, 255, .13);



  backdrop-filter:

    blur(30px);



  border-radius:

    30px;



  overflow: hidden;



}

.title {


  text-align: left;


  margin-bottom: 45px;


}



.title h1 {


  font-family:

    Arial,
    sans-serif;



  font-weight: 700;



  font-size: 40px;



  color: white;



  letter-spacing: 5px;



  margin: 0 0 14px;



}



.title h2 {


  font-size: 18px;


  font-weight: 400;


  letter-spacing: 4px;


  color: white;


  margin: 0;



}




.form {


  display: flex;


  flex-direction: column;


  gap: 16px;



}



input {


  height: 46px;


  border-radius: 25px;



  border: none;



  padding:

    0 20px;



  background:

    rgba(255, 255, 255, .25);



  color: white;



  font-size: 15px;


  outline: none;



}



input::placeholder {


  color:

    rgba(255, 255, 255, .8);


}



.form button {


  height: 48px;


  border: none;


  border-radius: 25px;


  background:

    #0033A0;



  color: white;



  font-size: 16px;


  font-weight: 600;



  cursor: pointer;



}





.divider {


  margin:

    35px 0 25px;


  text-align: center;


  color:

    rgba(255, 255, 255, .8);



}




.social {


  display: flex;


  justify-content: center;


  gap: 30px;


}




.social-btn {


  width: 55px;


  height: 55px;


  border-radius: 50%;


  border: none;



  background:

    rgba(255, 255, 255, .25);



  display: flex;


  align-items: center;


  justify-content: center;



  cursor: pointer;



}



.social-btn svg {


  width: 26px;


  height: 26px;


}





.terms {


  margin-top: 35px;



  text-align: center;



  font-size: 11px;



  line-height: 1.5;



  color:

    rgba(255, 255, 255, .65);



}
</style>