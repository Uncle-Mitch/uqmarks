const tblResult = document.getElementById("tblQuiz");
const Qtotalnum = document.getElementById("Qtotalnum");
const Qcount = document.getElementById("Qcount")

function changeQuiz() {
    var rowCount = tblResult.rows.length -1;
    var numOfQuiz = parseInt(Qtotalnum.value);
    if (numOfQuiz > 50) {
        numOfQuiz = 50;
        Qtotalnum.value = 50;
    }
    if (rowCount < numOfQuiz) {
        for (let i = rowCount + 1; i < numOfQuiz + 1; i++) {
            var bob = '<tr> <td class="quiz-label is-vcentered">Quiz '+i+'</td>  <td class="is-vcentered"><input onchange="calculate()" name="score" class="input score-input" type="text" placeholder="10/15" style="width: 100%;"></td> <td class="is-vcentered" name="score-percentage">0.00%</td> </tr>';
            tblResult.insertRow(-1).innerHTML = bob;
        }
    }

    if (rowCount > numOfQuiz) {
        for (let i = numOfQuiz; i < rowCount; i++) {
            tblResult.deleteRow(-1);
        }
    }

    Qcount.value = numOfQuiz;
}

function changeCount() {
    var numOfQuiz = parseInt(Qtotalnum.value);
    var numCount = parseInt(Qcount.value);
    if (numCount > numOfQuiz) {
        Qcount.value = numOfQuiz;
    }
    calculate();
}

const scores = document.getElementsByName("score");
const scoresPercent = document.getElementsByName("score-percentage");

function calculate(){
  let total_score = 0.00
  let undecided = 0.00
  var scoresArr = [];
  var numCount = parseInt(Qcount.value);
  var numOfQuiz = parseInt(Qtotalnum.value);


  for (let i = 0; i < scores.length; i++) {
    var resultArray = scores[i].value .split("/");

    if (resultArray.length != 2 && scores[i].value.length != 0) {
        scores[i].classList.add("is-danger");
    } else if (scores[i].classList.contains('is-danger')) {
        scores[i].classList.remove("is-danger");
    }

    let scoreStr = resultArray[0];
    let maxScoreStr = resultArray[1];

    // Filter the score, determine %
      if ((! isNaN(parseFloat(scoreStr))) && (! isNaN(parseFloat(maxScoreStr)))) {
        let score = parseFloat(scoreStr);
        let maxScore = parseFloat(maxScoreStr);

        if (score > maxScore) {
            scores[i].value = maxScore + "/" + maxScore
            scoresArr[i] = 1;
        }
        else if (score < 0.0) {
            scores[i].value = "0" + "/" + maxScore
            scoresArr[i] = 0.0;
        }
        else {
            scoresArr[i] = score/maxScore;
        }
        scoresPercent[i].innerText = (scoresArr[i]*100).toFixed(2) + "%"
      }
  }

  let numToRemove = numOfQuiz - numCount;
  var goodScores = scoresArr.sort((a,b) => a + b)
  // sort array to get eliminate values
  if (numToRemove > 0) {
    goodScores = goodScores.slice(0, numCount);
  }

  total_score = goodScores.reduce((pv, cv) => pv + cv, 0);
  total_score = (total_score/numCount) * 100
  total_score = total_score.toFixed(2);

  document.getElementById("lbltotalScore").innerText = "Total Score: " + parseFloat(total_score) + '%';
  return false;
}