document.getElementById("courseform").addEventListener("submit", function(e) {
    e.preventDefault();
    window.location.href = "/redirect";
    return false;
  });