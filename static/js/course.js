const scores = document.getElementsByName("score");

function calculate(){
  let total_score = 0.00
  let undecided = 0.00
  for (let i = 0; i < scores.length; i++) {
    let weight = parseFloat((scores[i].dataset.weight))
    if (scores[i].disabled === false) {
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
      } else if (scores[i].disabled === false) {
        undecided += weight/100
      }
   }
  }




  for (let i = 2; i <= 7; i++) {
    let cutoff = parseInt(document.getElementById(i.toString() + "-cutoff").innerText);
    let required = document.getElementById(i.toString() + "-required");
    let score = document.getElementById(i.toString() + "-score");
    let row = document.getElementById('row-' + i.toString());

    if (total_score >= cutoff) {
      required.innerText = 0;
      score.innerText = '0/' + parseInt(undecided * 100).toString();
      row.style.backgroundColor = "#68FF77";
    } else {
      let required_score = Math.ceil((cutoff - total_score)/ undecided);
      required.innerText = required_score;
      score.innerText = Math.ceil((required_score * undecided)).toString() + '/' + (parseInt(undecided*100)).toString();
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

function onStart() {
  for (let i = 0; i < scores.length; i++) {
    if (scores[i].dataset.weight.toLowerCase().indexOf("%") === -1) {
      scores[i].disabled = true;
    }
    else if (scores[i].dataset.weight.toLowerCase() == "10%") {
      scores[i].disabled = true;
    }
  }
return false;
}
onStart();