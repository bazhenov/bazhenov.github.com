set term svg enhanced size 800,300 lw 1.5
set output 'multiple-modes.svg'

set grid
set key left top

set datafile separator ',

#set log y 10;

set yrange [0:12]
set xrange [0:800]

set ylabel "time (us.)"
set xlabel "observation no"

set title "Algorithm execution time"
plot "./multiple-modes.csv" using ($1 / 1000) title "time to execute" with linespoints pt 4 ps 0.4 lw 0.2
