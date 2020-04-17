library(ggplot2)
data <- read.csv('/Archive/Src/RoadTools/roadtools/core/out.csv')

 ggplot(data, aes(index, y = value, color = variable)) +
   geom_point(aes(y = elev_ellip, col = "elev_ellip")) +
   geom_point(aes(y = elev_orto, col = "elev_orto"))
