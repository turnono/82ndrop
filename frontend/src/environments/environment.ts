export const environment = {
  production: true,
  apiUrl: 'https://drop-api-service-855515190257.us-central1.run.app', // FastAPI backend URL
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
};
