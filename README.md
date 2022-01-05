# Power Systems Python  
  
A set of tools for calculating power system impedances, faults, pole spans, pole line stress and strain, and voltage drops.

I had uploaded an older version some time ago, then I had overhauled the program extensiviely during my time working for an electric cooperative. I thought the code had been lost but I happened to find a backup USB drive with an nearly finished version. I have added some slight modifications to the code for compatablility over the last few months with Python 3.9 and am now at a point I I am ready to upload and begin reqorking the examples.  

I do also have some utilities that I had created to pull data from a Milsoft Windmil database that I may upload in the coming months. I can no longer test the milsoft code but it will be made available.  

It is my goal that this will aid some smaller cooperatives and municipalities in performing routine calculations.  

## Basic Overview  

### PoleCad  
<ol>
<li>There is an overview document titled Pole Calculator Basic which explains file structure</li>
<li>The poleLaunch function will begin the program and if the data is correct will create top view stress, strain, and guying diagrams for each study pole, a csv file will also be created containing raw data
<ol>
<li>test1 and test2 scripts and folders show basic examples of the calculator</li>
</ol></li>
<li>The spanLaunch function will create a csv file that contains span information</li>
</ol>

### powerCad
<ol>
<li>There curently isnt documentation on the fault calculation and time coordination curve functions, I am planning on writting these up</li>
<li>The time curve coordination will display a graph and optional reference points
<ol>
<li>testtcc script and foldes show a basic example of the time coordination curve</li>
<li>Note that the ocdevdb contains the curve list database in the tcctest folder</li>
<li>It also shows example calls to calculate some impedances and fault currents</li>
</ol></li>
<li>The voltage drop function has an example script called vDrop</li>
<li>The impedance calculator based on csv conductor files was never completed fully and requires further development</li>
</ol>

### Future Plans

<ol>
<li>Add additional documentation</li>
<li>Add equipment at voltage levels other then 7.2kV</li>
<li>Complete the impedance calulation functions</li>
</ol>
