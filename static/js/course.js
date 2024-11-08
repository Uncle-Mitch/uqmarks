const scores = document.getElementsByName("score");
const score_switches = document.getElementsByName("score-switch");

function calculate(){
  let total_score = 0.00
  let decided = 0
  let total_weights = 0
  for (let i = 0; i < scores.length; i++) {
    let weight = parseFloat((scores[i].dataset.weight))
    if (scores[i].disabled === true) {
      continue
    }
    else {
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
        decided += weight;
      } 
      total_weights += weight;
   }
  }

  total_weights = Math.round(total_weights);
  // Check if total weights of items != 100 marks
  if (total_weights < 100) {
    document.getElementById("invalid-weight-warning").classList.remove('is-hidden');
  }
  else {
    document.getElementById("invalid-weight-warning").classList.add('is-hidden');
  }

  // Cap required calculated score to be 100 marks maximum. (e.g. cannot be 1/101 required)
  // Useful for courses with optional marks / best out of X quizes.
  let undecided = Math.max(100-decided, 0); 



  for (let i = 2; i <= 7; i++) {
    let cutoff = parseInt(document.getElementById(i.toString() + "-cutoff").innerText);
    let required = document.getElementById(i.toString() + "-required");
    let score = document.getElementById(i.toString() + "-score");
    let row = document.getElementById('row-' + i.toString());

    if (total_score >= cutoff) {
      required.innerText = 0;
      score.innerText = '0/' + parseInt(undecided).toString();
      row.style.backgroundColor = "#68FF77";
    } else {
      let required_score = Math.ceil((cutoff - total_score)/ undecided * 100);
      required.innerText = required_score;
      score.innerText = Math.ceil((required_score * undecided / 100)).toString() + '/' + (parseInt(undecided)).toString();
      if (required_score > 100) {
        // The user cannot get the grade
        row.style.backgroundColor = "#FF3A3D";
      } else {
        row.style.backgroundColor = "#FFFFFF";
      }

    }
  }

  document.getElementById("lbltotalScore").innerText = "Total Score: " + +total_score.toFixed(2) + '%';
  return false;
}

function toggleDisable(checkbox) {
  const scoreInput = checkbox.closest('tr').querySelector('.score-input');
  scoreInput.disabled = ! checkbox.checked;
  calculate(); // Re-calculate with updated weights.
}

function onStart() {
  for (let i = 0; i < scores.length; i++) {
    if (scores[i].dataset.weight.toLowerCase().indexOf("%") === -1) {
      scores[i].disabled = true;
      scores[i].title = "A VALID percentage weight format has not been detected.";
      score_switches[i].disabled = true;
      score_switches[i].checked = false;
      score_switches[i].title = "A VALID percentage weight format has not been detected.";
    }
    else if (scores[i].dataset.weight.toLowerCase() == "0%") {
      scores[i].disabled = true;
      scores[i].title = "A VALID percentage weight format has not been detected.";
      score_switches[i].disabled = true;
      score_switches[i].checked = false;
      score_switches[i].title = "A VALID percentage weight format has not been detected.";
    }
  }
  calculate();
return false;
}

document.addEventListener('DOMContentLoaded', function() {
  onStart();
});
