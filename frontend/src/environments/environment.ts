export const environment = {
  production: false,
  staging: true,
  apiUrl: 'http://localhost:8000',
  paystack: {
    publicKey: 'pk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', // Replace with your Paystack public key
    secretKey: 'sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', // Replace with your Paystack secret key
  },
  firebase: {
    apiKey: 'AIzaSyDGaH72jq3Ev-Jue-5qm72OzpRCWzQMh9U',
    authDomain: 'taajirah.firebaseapp.com',
    databaseURL:
      'https://taajirah-default-rtdb.europe-west1.firebasedatabase.app',
    projectId: 'taajirah',
    storageBucket: 'taajirah.appspot.com',
    messagingSenderId: '855515190257',
    appId: '1:855515190257:web:2c01b97a96acc83556ea50',
    measurementId: 'G-SP3FWBJNT3',
  },
  debugMode: true,
  logLevel: 'DEBUG',
};
