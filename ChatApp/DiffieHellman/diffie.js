import {Crypto} from 'crypto'
var _private = {}
// _private.crypto = window.crypto && window.crypto.getRandomValues;
var primes = {
    5:{
      "prime": 1,
      "generator":2
    },
    14:{
      "prime":7,
      "generator":2
    },
    15:{
      "prime":13,
      "generator":2
    }
  }
  
  class DiffieHellman{
    constructor(group = 14){
      // if(group in primes==false){
      // throw 'Unsupported Group';
      // }
      this.prime = primes[group]['prime']
      this.generator = primes[group]['generator']
      this.private_key = window.crypto.getRandomValues;
    }
    get_name(){
      console.log(this.prime);
    }
    get_private_key(){
      
    }
  }
  let bp = new DiffieHellman()
  console.log(bp.private_key)
  