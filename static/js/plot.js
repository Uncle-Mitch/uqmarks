function resizeIframe(obj) {
    obj.style.height = obj.contentWindow.document.documentElement.scrollHeight + 'px';
}

document.addEventListener('DOMContentLoaded', function () {
    var iframe = document.getElementById('analytics-iframe');

    iframe.addEventListener('load', function () {
        var iframeWindow = iframe.contentWindow;

        // Check if the button is present inside the iframe
        var semesterBtn = iframeWindow.document.getElementById('semester-btn');

        if (semesterBtn) {
            // Add a click event listener to the button inside the iframe
            semesterBtn.addEventListener('click', function () {
                console.log('Semester button clicked inside the iframe');
                // Additional actions here
            });
        } else {
            console.error('Button with ID "semester-btn" not found inside the iframe.');
        }
    });
});
