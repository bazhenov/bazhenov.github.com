QUnit.test( "ProportionTest should correctly identify equal proportions", function( assert ) {
	var r = twoProportionsHT([100, 100], [100, 100])
  	assert.equal(r.rejectNull, false, "В данном случае мы не должны отклонять нулевую гипотезу");
  	assert.ok(r.pValue > 0.999 && r.pValue < 1.001, "p-value должно быть равно 1 [" + r.pValue + "]");

  	r = twoProportionsHT([100, 100], [200, 200])
  	assert.equal(r.rejectNull, false, "В данном случае мы не должны отклонять нулевую гипотезу");
  	assert.ok(r.pValue > 0.999 && r.pValue < 1.001, "p-value должно быть равно 1 [" + r.pValue + "]");
});

QUnit.test( "ProportionTest should correctly identify non-equal proportions", function( assert ) {
	var r = twoProportionsHT([1000, 1000], [1000, 850])
  	assert.equal(r.rejectNull, true, "В данном случае мы должны отклонить нулевую гипотезу");
  	assert.ok(r.pValue > 0.011 && r.pValue < 0.012, true, "p-value должно быть ~0.0118 [" + r.pValue + "]");
});