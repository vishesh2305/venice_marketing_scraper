const mongoose = require('mongoose')

const Schema = mongoose.Schema

const studentSchema = new Schema({
    username: {
        type: String,
        required: true
    },
    email: {
        type: String,
        required: true
    },
    password: {
        type: String,
        required: true
    },
    studentId: {
        type: Number,
        required: true
    },
    studentName: {
        type: String,
        required: true
    }
},  { timestamps:true}
)

module.exports = mongoose.model("Students", studentSchema) 