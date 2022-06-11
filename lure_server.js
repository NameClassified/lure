const http = require("http");
const aws = require("aws-sdk");


const host = 'localhost';
const port = 8080;

const s3 = new aws.S3({
    region: 'us-east-2',
    accessKeyId:"XXXXXXXXXXXXXXXXXXXX",
    secretAccessKey:"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    
});
function getImage(key){
    var get_params = {
        Bucket: 'lure-cjpan',
        Key: key,
        Expires: 60*5
    }
    var objData = '';
   s3.getObject(get_params,function(err,data) {
       objData=data.Body.toString('base64');

   });
    return objData;
  }
async function listAllObjectsFromS3Bucket(bucket, prefix, res) {
    let isTruncated = true;
    let marker;
    while(isTruncated) {
      let params = { Bucket: bucket };
      if (prefix) params.Prefix = prefix;
      if (marker) params.Marker = marker;
      try {
        const response = await s3.listObjects(params).promise();
        let startHTML="<html><body></body>";
        var html = startHTML
        
        response.Contents.forEach(item => {
            
          console.log(item.Key);
          //var image = await(getImage(item.Key))
            //image="<img src='data:image/jpeg;base64," + encode(img.Body) + "'" + "/>";
          //var url ='https://lure-cjpan.s3.us-east-2.amazonaws.com/'+item.Key;
          var url = s3.getSignedUrl('getObject', {
                Bucket: 'lure-cjpan',
                Key: item.Key,
                Expires: 60*5
          });
          img = '<img src='+url+'>';
          //var img = "<img src='data:image/jpeg;base64," + image + "/>";

          html= html + img;
            
          
        

        
        isTruncated = response.IsTruncated;
        if (isTruncated) {
          marker = response.Contents.slice(-1)[0].Key;
        }
        })
        html = html + "</body></html>";
        return html
    
    }
     catch(error) {
        throw error;
      }
    }
  }
  
  
const requestListener = async function (req, res) {
    
    
    html = await listAllObjectsFromS3Bucket('lure-cjpan', '');
    console.log(html);
    res.writeHeader(200, {"Content-Type": "text/html"});  
    res.write(html.toString());  
    res.end();
};

const server = http.createServer(requestListener);
server.listen(port, host, () => {
    console.log('Server is running on http://${host}:${port}')
});