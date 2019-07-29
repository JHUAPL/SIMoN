
#def populationfunction(logisticpopulation):
#    pop={}
 #   sum = 0
 #   for i in logisticpopulation.keys():
 #       N = logisticpopulation[i] #this is the county population 
 #       k = 300000000/3007 #this scales the max capacity to the county level (there are 3007 US counties)
 #       r = 1.0061 #this is the growth rate
 #       pop[i] = r*N*((k-N)/k) #this is the equation 

 #   return pop

#def populationfunction(logisticpopulation):
#    pop={}
#    sum = 0
#    for i in logisticpopulation.keys():
#        sum += logisticpopulation[i]
        #print(sum)
#        N = logisticpopulation[i] #this is the county population
#        k = (N/sum) *300000000 #this scales the max capacity to the county level (there are 3007 US counties)
 #       r = 1.0061 #this is the growth rate
  #      pop[i] = r*N*((k-N)/k) #this is the equation

   # return pop

def populationfunction(population):
    pop={}
    mysum = 0
    for i in population.keys():
        #or j in logisticpopulation.keys()[i]:
        mysum += population[i]  
    
    for i in population.keys():
        N = population[i] #this is the county population
        k = (N/mysum) *400000000 #this scales the max capacity to the county level (there are 3007 US counties)
        r = 1.0071 #this is the growth rate
        pop[i] = N + r*N*((k-N)/k) #this is the equation
    return pop
