const path = require("path");
const fs = require("fs");

const handlebars = require("handlebars");

const multer = require('multer')
const upload = multer({});

const request = require('request')

const http = require('http')

const parody_names = [
    'Gargle',
    'Gaggle',
    'Gravel',
    'Garble',
    'Gödel'
];

function get_search_engine_name() {
    return parody_names[Math.floor(Math.random() * parody_names.length)]
}

function assemble_bars(bars, data) {
    // Assemble template
    let template = handlebars.compile(bars)
    
    // Fill the template
    return template(data);
}

function assemble_page(bars, content) {
    // Generate data
    let data = {
        content: content
    };
    
    return assemble_bars(bars, data);
}

function assemble_search_page(type) {
    let bars = read_file('layouts/search_page.handlebars');
    let search_box = read_file(`layouts/searchbox_${type}.handlebars`);

    search_engine_name = get_search_engine_name() + (type == 'img' ? '<sub>Images</sub>' : '')

    console.log(search_box)
    
    return assemble_bars(bars, {
        search_box : search_box,
        search_engine_name : search_engine_name
    });
}

function assemble_results_page(results) {
    let page_bars = read_file('layouts/search_results.handlebars');
    let img_bars = read_file('layouts/search_result_img.handlebars');

    bars = {
        'image' : read_file('layouts/search_result_img.handlebars'),
        'text' : read_file('layouts/search_result_txt.handlebars')
    }

    // console.log(results)

    listing = results["files"].map(dat => {
        fname = dat['url'];
        type = dat['type'];

        brs = bars[type];

        splt = fname.split('/');
        
        let title = splt[0];
        if (splt.length > 1) {
            title = splt[splt.length-2];
        }

        let desc = splt[splt.length-1];
        
        return assemble_bars(brs, {
            'link' : fname,
            'title' : title,
            'desc' : desc
        });
    }).join('\n');

    search_engine_name = get_search_engine_name() + (type == 'img' ? '<sub>Images</sub>' : '')

    return assemble_bars(page_bars, {
        content : listing,
        search_engine_name : search_engine_name
    });
}

function read_file(fname) {
    return fs.readFileSync(path.resolve(fname), 'utf-8')
}

function runExpectingSuccess(res, operation) {
    try {
        operation();
    } catch (error) {
        console.log(error);
        res.status(500).json({error: '500 Internal Server Error'});
    }
}

function makeSearchRequest(data, route, res, callback) {
    // Form POST params
    const params = {
        hostname : 'localhost',
        port : 8000,
        path : '/',
        method : 'POST',
        headers : {
            'Content-Type' : 'application/json',
            'Content-Length' : data.length
        }
    }

    const search_request = http.request(params, (resp) => {
        console.log(`statusCode: ${resp.statusCode}`);

        if (resp.statusCode != 200) {
            res.status(500).json({error: '500 Internal Server Error'});
            return
        }

        resp.on('data', dta => 
            runExpectingSuccess(res, () => callback(dta))
        );

    });

    console.log('Performing request:');
    console.log(params);
    
    runExpectingSuccess(res, () => {
        search_request.write(data)
        search_request.end()
    });
}

module.exports = app => {
    // Get the search page
    app.get(['/', '/images'], function (req, res) {
        // Use image search by default
        let page = assemble_search_page('img')
        res.send(page)
    });

    app.get(['/search'], function(req, res) {
        let page = assemble_search_page('txt');
        res.send(page);
    });

    // Posting data returns a search result
    app.post('/images', upload.single('image'), async function(req, res) {
        if (!req.file) {
            res.status(401).json({error: 'Please provide an image'})
            return
        }
        
        const img_buff = req.file.buffer
        
        const data = JSON.stringify({
            count : 10,
            image : img_buff.toString('base64')
        });
        
        makeSearchRequest(data, '/images', res, (dta) => {
            console.log(dta);
            json = JSON.parse(dta);
            page = assemble_results_page(json)
            res.send(page)
        });
    });

    app.post('/search', (req, res) => {
        if (!req.body.text) {
            res.status(401).json({error: 'Please provide text', body: req.body});
            return
        }

        const query = req.body.text;

        console.log('Query: "' + query + '"');

        const data = JSON.stringify({
            count : 10,
            text  : query
        });

        makeSearchRequest(data, '/search', res, dta => {
            json = JSON.parse(dta);
            page = assemble_results_page(json);
            res.send(page);
        });
    });

};

