obj = document.getElementById('analytics-iframe');

obj.contentWindow.addEventListener('DOMContentLoaded', function () {
    //console.log(obj.contentWindow.document.body.scrollHeight);
    //obj.style.height = obj.contentWindow.document.documentElement.scrollHeight + 'px';
    document.getElementById('spinner').style.display = 'none';
    console.log('TESTING');
    document.getElementById('analytics-iframe').style.visibility = 'visible';
});

