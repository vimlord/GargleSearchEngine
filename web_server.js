
const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');

const configRoutes = require('./routes');

// Get the port number
const port = process.env.port || 8080;

// Get the express application
const app = express();

// Use JSON parsing
app.use(bodyParser.urlencoded());
app.use(bodyParser.json());

// Stylesheet for the site will be served if it exists
app.use('/site.css', (req, res) => {
    res.sendFile(path.resolve('dist/site.css'));
});

// Use static content for images
const img_root = path.join(process.env.HOME, '.keras/datasets/flower_photos/')
app.use('/images/', express.static(img_root));

// Configure the routes
configRoutes(app);

// Listen on the defined port
app.listen(port, () => {
    console.log(`Web server running on port ${port}`);
});

