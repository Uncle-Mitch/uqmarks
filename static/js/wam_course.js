const all_scores = document.getElementsByClassName("score-input");
const all_score_switches = document.getElementsByClassName("score-switch");
window.isInternalReload = false;
window.loadingCourses = true;
window.changesMade = false;

function calculate(code){
  let scores = document.getElementsByName(code + "-score");
  let total_score = 0.00
  let decided = 0.00
  let total_weights = 0.00
  const resultsDict = {};
  for (let i = 0; i < scores.length; i++) {
    let weight = parseFloat((scores[i].dataset.weight))
    if (scores[i].disabled === true) {
      continue
    }
    var resultArray = scores[i].value.split("/");

    if (resultArray.length != 2 
      && scores[i].value.length != 0 
      && resultArray.length != 1) {
      scores[i].classList.add("is-danger");
      continue;
    } else if (scores[i].classList.contains('is-danger')) {
        scores[i].classList.remove("is-danger");
    }

    let scoreStr = resultArray[0];
    let maxScoreStr = null;
    if (resultArray.length == 2) {
      maxScoreStr = resultArray[1];
    }

    // If they provided numerator but not denominator of fraction
    // and vice versa
    if (scores[i].value.includes("/") 
        && (isNaN(parseFloat(maxScoreStr)) || isNaN(parseFloat(scoreStr)))) {
      scores[i].classList.add("is-danger");
      continue;
    }

    

    if (! isNaN(parseFloat(scoreStr))) {
      let score = parseFloat(scoreStr);
      
      // If the user decided to do fractions
      if (maxScoreStr != null ) {
        score = (score*100)/parseFloat(maxScoreStr);
      }

      // Bound the scores to 0 and 100% respectively.
      if (score > 100){
        score = 100
        scores[i].value = score + "%" // Explicit % sign for users
      } else if (score < 0){
        score = 0
        scores[i].value = score  + "%"
      }
      total_score += score*(weight/100);
      decided += weight/100;
    } 
    total_weights += weight/100;
}

  // Check if total weights of items != 100 marks
  if (total_weights < 1) {
    document.getElementById(code + "-invalid-weight-warning").classList.remove('is-hidden');
  }
  else {
    document.getElementById(code + "-invalid-weight-warning").classList.add('is-hidden');
  }
  
  document.getElementById(code + "-lbltotalScore").innerText =  total_score.toFixed(2) + '%';
  calculateTotalScores();
  return false;
}

function toggleDisable(checkbox) {
  const scoreInput = checkbox.closest('tr').querySelector('.score-input');
  scoreInput.disabled = ! checkbox.checked;
  let code = scoreInput.dataset.code;
  calculate(code); // Re-calculate with updated weights.
}

function calculateTotalScores() {
  let totalScores = document.getElementsByClassName("total-score");
  let grandTotal = 0;
  window.changesMade = true;

  for (let i = 0; i < totalScores.length; i++) {
    // Remove the unnecessary text to retrieve the number
    var score = totalScores[i].innerHTML.split("%")[0];
    score = parseFloat(score);
    if (!isNaN(score)) {
      grandTotal += score;
    }
  }
  grandTotal /= totalScores.length;

  document.getElementById("final-lbltotalScore").innerHTML = "Your WAM: " + grandTotal.toFixed(2) + '%';
}

async function onStart() {
  for (let i = 0; i < all_scores.length; i++) {
    if (all_scores[i].dataset.weight.toLowerCase().indexOf("%") === -1) {
      all_scores[i].disabled = true;
      all_scores[i].title = "A VALID percentage weight format has not been detected.";
      all_score_switches[i].disabled = true;
      all_score_switches[i].checked = false;
      all_score_switches[i].title = "A VALID percentage weight format has not been detected.";
    }
    else if (all_scores[i].dataset.weight.toLowerCase() == "0%") {
      all_scores[i].disabled = true;
      all_scores[i].title = "A VALID percentage weight format has not been detected.";
      all_score_switches[i].disabled = true;
      all_score_switches[i].checked = false;
      all_score_switches[i].title = "A VALID percentage weight format has not been detected.";
    }
  }

  let savedScores = null;
  try {
    const response = await fetch('/api/wam/get_scores', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
  
    const data = await response.json();
    savedScores = data ? data.scores : null;
  } catch (e) {

  }
  
  for (let i = 0; i < all_scores.length; i++) {
    const currentScore = all_scores[i];
    const currentCode = currentScore.dataset.code;
    const itemNum = currentScore.dataset.item;

    let score = null;

    if (savedScores && savedScores[currentCode]) {
      const currentItem = savedScores[currentCode][itemNum]
      score = currentItem['score']
      all_scores[i].disabled = Boolean(currentItem['disabled'])
      all_score_switches[i].checked = !Boolean(currentItem['disabled'])

      if (currentItem['collapsed']) {
        const cardId = currentCode + "-card";
        const cardContent = document.querySelector(`#${cardId} .card-content`);
        cardContent.classList.add('is-hidden');
      }
      
    }

    all_scores[i].value = score;
    calculate(currentCode);
    
  }
  calculateTotalScores();
  window.changesMade = false;
return false;
}

function attachCardListener() {
  const toggleButtons = document.querySelectorAll('.card-header');
  // Collapsible buttons
  toggleButtons.forEach(button => {
    button.addEventListener('click', () => {
      changesMade = true;
      const cardId = button.getAttribute('data-card');
      const cardContent = document.querySelector(`#${cardId} .card-content`);
      
      cardContent.classList.toggle('is-hidden');
      const icon = button.querySelector('i');
      if (cardContent.classList.contains('is-hidden')) {
        icon.classList.remove('fa-angle-up');
        icon.classList.add('fa-angle-down');

      } else {
        
        icon.classList.remove('fa-angle-down');
        icon.classList.add('fa-angle-up');
      }
    });
  });

  // Delete buttons
  const deleteButtons = document.querySelectorAll('.card-delete-icon');
  deleteButtons.forEach(button => {
    button.addEventListener('click', () => {
      const courseCode = button.dataset.code;
      const semester = button.dataset.semester;
      changesMade = true;

      fetch('/api/wam/remove_course', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/x-www-form-urlencoded', // Important for form data
          },
          body: new URLSearchParams({ // Convert form data to URL-encoded format
              'wam_semester': semester,
              'wam_course_code': courseCode,
          }),
      })
      .then(response => response.json())
      .then(data => {
          if (data.success) {
              window.isInternalReload = true;
              location.reload(); // Reload page to show new course
          } else {
              alert("Error removing course: " + data.message);
          }
      })
      .catch(error => {
          console.error('Error:', error);
          alert("An error occurred while adding the course.");
      })      
    });

    
  })
}

function formHandler() {
  const courseForm = document.getElementById('courseform');
  if (!courseForm) {
    return;
  }
  
  courseForm.addEventListener('submit', function(event) {
      event.preventDefault(); // Prevent default form submission

      
      const semesterInput = document.getElementById('wam_semester');
      const courseCodeInput = document.getElementById('wam_course_code');
      const submitBtn = document.getElementById('submitBtn');
      const inputContainer = document.getElementById('input_container');

      const semester = semesterInput.value;
      const courseCode = courseCodeInput.value;
      inputContainer.classList.add("is-loading");
      

      if (!semester || !courseCode) {
          alert("Please select a semester and enter a course code.");
          return;
      }
      
      semesterInput.disabled = true;
      courseCodeInput.disabled = true;
      submitBtn.disabled = true;

      const showErrorMessage = (message) => {
        const errorMessageLabel = document.getElementById('error-message')
        errorMessageLabel.innerHTML = message;
        courseCodeInput.classList.add('is-danger');
      }
      
      // Send data to Flask backend
      fetch('/api/wam/add_course', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/x-www-form-urlencoded', // Important for form data
          },
          body: new URLSearchParams({ // Convert form data to URL-encoded format
              'wam_semester': semester,
              'wam_course_code': courseCode,
          }),
      })
      .then(response => response.json())
      .then(data => {
          if (data.success) {
              window.isInternalReload = true;
              location.reload(); // Reload page to show new course
          } else {
            showErrorMessage(data.error);
          }
      })
      .catch(error => {
        showErrorMessage("An unexpected error has occurred.");
      }).finally(() => {
        semesterInput.disabled = false;
        courseCodeInput.disabled = false;
        submitBtn.disabled = false;
        inputContainer.classList.remove("is-loading");
      });
      
  });
}

document.addEventListener('DOMContentLoaded', async function() {
  onStart();
  attachCardListener();
  formHandler();
});

async function save_scores() {
  let coursesList = {};
  for (let i = 0; i < all_scores.length; i++) {
    var resultArray = all_scores[i].value.split("/");
    const code = all_scores[i].dataset.code
    let scoreStr = resultArray[0];
    if (!coursesList[code]) {
      coursesList[code] = { results: {} };
    }
  
    if (!coursesList[code]["results"]) {
      coursesList[code]["results"] = {};
    }   
    const cardId = code + "-card";
    const cardContent = document.querySelector(`#${cardId} .card-content`);
    const cardCollapsed = cardContent.classList.contains('is-hidden');
    coursesList[code]["results"][`${all_scores[i].dataset.item}`] = {"score": `${all_scores[i].value}`, "disabled": all_scores[i].disabled, "collapsed": cardCollapsed};
  }

  for (const code of Object.keys(coursesList)) {
    const scores = coursesList[code]["results"]
    await fetch('/api/wam/save_score', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded', // Important for form data
        },
        body: new URLSearchParams({ // Convert form data to URL-encoded format
            'wam_course_id': code,
            'scores': JSON.stringify(scores),
        }),
    })
  }
  
}



// Ensures scores are saved to localStorage
window.addEventListener('beforeunload', async function (event) {
  if (window.isInternalReload || !window.changesMade) {
    return;
  }
  event.preventDefault();
  event.stopPropagation();
  save_scores();
});


document.getElementById("saveButton").addEventListener("click", async function(event) {
  event.target.classList.add("is-loading");
  save_scores().then( () => {
    event.target.classList.remove("is-loading");
    window.changesMade = false;
  })
})
