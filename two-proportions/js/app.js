function twoProportionsHT(v1, v2) {
	// Определяем 0-й элемент за успех, а 1-й за неудачу
	var n1 = v1[0] + v1[1];
	var n2 = v2[0] + v2[1];
	var pp = (v1[0] + v2[0]) / (n1 + n2);
	var p1 = v1[0] / n1;
	var p2 = v2[0] / n2;
	var standardError = Math.sqrt((pp * (1 - pp) / n1) + (pp * (1 - pp) / n2));
	console.log(standardError);
	zScore = (p1 - p2) / standardError;
	pValue = 2 * cdf(-Math.abs(zScore), 0, 1);
	return {pValue: pValue, rejectNull: pValue < 0.05}

}

function erf(x) {
  var sign = (x >= 0) ? 1 : -1;
  x = Math.abs(x);

  var a1 =  0.254829592;
  var a2 = -0.284496736;
  var a3 =  1.421413741;
  var a4 = -1.453152027;
  var a5 =  1.061405429;
  var p  =  0.3275911;

  // A&S formula 7.1.26
  var t = 1.0/(1.0 + p*x);
  var y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);
  return sign * y; // erf(-x) = -erf(x);
}

function cdf(x, mean, variance) {
  return 0.5 * (1 + erf((x - mean) / (Math.sqrt(2 * variance))));
}