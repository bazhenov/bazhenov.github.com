set term svg enhanced size 800,600 lw 1.5
set output 'outliers.svg'
set grid

set key left top

set datafile separator ',

set multiplot

set xrange [250:400]

set ylabel "time (us.)"
set xlabel "observation no"

set title "Diff algorithm time"
set size 1,0.6
set origin 0,0
plot "./outliers.csv" using ($3 / 1000) title "time ∆ (candidate - baseline)" with linespoints ps 0.7 lw 0.7

set log y 10

set title "Algorithm execution time"
set size 1,0.4
set origin 0,0.6
plot "./outliers.csv" using ($1 / 1000) title "base" with linespoints ps 0.3 lw 0.7, \
     "./outliers.csv" using ($2 / 1000) title "candidate" with linespoints ps 0.3 lw 0.7
