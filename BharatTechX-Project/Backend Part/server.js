require('dotenv').config()
const express = require('express');

const mongoose = require('mongoose');

const appRoutes = require('./routes/routes');
const exp = require('constants');
const { error } = require('console');


const app = express();

app.use(express.json());

app.use((req, res, next)=> {
    console.log(req.path, req.method)
    next()
})

app.use( '/api/routes',appRoutes)


//Connect to Database
mongoose.connect(process.env.MONG_URI)
.then(() => {

    //Listen to Requests
    app.listen(process.env.PORT, () => {
        console.log("Connected to DB and Listening on port 5000 !", process.env.PORT)
    });

})


.catch((error) => {
    console.log(error);
});