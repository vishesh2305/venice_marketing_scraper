const express = require('express');
const router = express.Router();

router.get("/", (req, res)=> {
    res.json({mssg: "Hello World"});
})

router.get('/:id', (req, res) => {
    res.json({mssg: "Get a Single request on particular id"})
})




router.post('/', (req, res) => {
    res.json({mssg: "Post a New request"})
});

router.delete('/:id', (req, res) => {
    res.json({mssg: "Delete a new Request"})
});

router.patch('/:id', (req,res) => {
    res.json({mssg: "Update a request"})
});


module.exports = router;