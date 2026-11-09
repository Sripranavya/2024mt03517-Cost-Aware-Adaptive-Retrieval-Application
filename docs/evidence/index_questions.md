# Questions behind the live indexes

The OpenSearch indexes hold **passages**, not questions: each HotpotQA question contributes
10 passages (2 supporting + 8 distractors). The questions below are the benchmark questions
whose passages are indexed, so these are the questions the live demo can answer well.
Source: the saved per-query results of the POMDP runs (`results/hpv2/test`, `results/hpv4/test200`,
`results/msv2/test`). F1 and hops are the POMDP's result for that question in that run.

| Index | Questions | Passages | Content |
|---|---|---|---|
| `hp-test` | 80 | 800 | HotpotQA test split (the first 80 in hash order) |
| `hp-t200` | 200 | 1,996 | HotpotQA test, n=200 (includes the 80 above) |
| `ms-test` | 60 | 651 | MS MARCO test split (single hop) |
| `hp-val` | 30 | 300 | HotpotQA validation split |

## HotpotQA, `hp-test` (80 questions)

| # | Question | POMDP F1 | Hops |
|---|---|---|---|
| 1 | Which documentary film came out first The Last Lions or Prophet's Prey ? | 1.00 | 2 |
| 2 | how many films has the director of "Girl 6" produced since 1983? | 0.80 | 2 |
| 3 | Which TV series directed and written by the same person as "Buffy the Vampire Slayer" starred Tahmoh Penikett? | 1.00 | 2 |
| 4 | What was the birth name of the ex-slave abolitionist featured in the art installation The Dinner Party? | 0.00 | 2 |
| 5 | What is the hometown of Duck Down Music artist and complex rapper Pharaohe Monch? | 1.00 | 4 |
| 6 | Where is the company that created Doravirine ( from? | 0.00 | 2 |
| 7 | Of what ethnicity is the founder of the Orchestra which debuted on January 1, 1988? | 1.00 | 2 |
| 8 | What English-American actor known for his role in "Raiders of the Lost Ark" starred in The Lodger? | 0.80 | 2 |
| 9 | Edward Marszewski is the editor-in-chief of Lumpen, who is the editor-in-chief of Saveur? | 0.00 | 2 |
| 10 | Beena Sarwar is the editor of a peace initiative sponsored by a newpaper based in what city? | 0.67 | 2 |
| 11 | Are Hot Rod and The Memory of Our People both magazines? | 1.00 | 2 |
| 12 | Who was the football manager that played in the Football League Cup in 1985 and managed to lead the Birmingham City Football Club's 103rd season to finish in the 18th position? | 0.67 | 2 |
| 13 | Where was the sports complex at which Will Brodie made his debut in the thirty-five point loss against Melbourne located? | 0.00 | 2 |
| 14 | The Extreme Centre: A Warning was a book by the activist who studied at which college? | 0.80 | 2 |
| 15 | Which poet is famous for "A Shropshire Lad" and is depicted in the play "The Invention of Love"? | 1.00 | 2 |
| 16 | On what date did the geological event, that caused the 2011 Japanese motorcycle Grand Prix to be rescheduled, take place ? | 1.00 | 2 |
| 17 | Which of the movie which has Rich Lee 3-D previsualizations was directed by Francis Lawrence? | 0.04 | 2 |
| 18 | Be Quick '28  football club is locayed in what province? | 1.00 | 2 |
| 19 | Were both Sinclair Research and the Wave Mate Bullet founded in the 1970s? | 0.00 | 2 |
| 20 | How long did the king who created the coins of the hawaiian dollar rule? | 0.00 | 2 |
| 21 | Where are people with ADolf Bestelmeyer's nationality from? | 1.00 | 2 |
| 22 | Which movie used more styles of animation and filming, James and the Giant Peach or Tangled ? | 1.00 | 2 |
| 23 | Who produced the 1998 British comedy starring the director of the feature film "Eddie the Eagle"? | 0.00 | 2 |
| 24 | What's the name of the differential equation that was developed by the German physicist who was the doctoral advisor to another German Physicist who identified the Stark effect? | 1.00 | 2 |
| 25 | What team did Robbie Keane play for after Inter Milan? | 0.00 | 2 |
| 26 | Do writers John O'Hara and Bobbie Ann Mason share the same nationality? | 1.00 | 2 |
| 27 | What was the country which has border with the village where an Austrian forest caretaker, naturalist, pseudoscientistref>Ronald Engert: "Die Forellenturbine als Prinzip der kostenlosen Energiegewinnung born? | 1.00 | 2 |
| 28 | What does the unique calendar system in Japan, who the first Emperor of Japan created, emphasize? | 0.73 | 2 |
| 29 | Which band has more members, Test Icicles or X Ambassadors? | 1.00 | 2 |
| 30 | Which is a comedy film, The Million Dollar Duck or Don Quixote? | 1.00 | 2 |
| 31 | The Westchester Knicks are a basketball team in a minor league basketball organization that was known as what from 2001 to 2005? | 0.89 | 2 |
| 32 | What is the primary role of the position played by Viktor Raychev for Lokomotiv Sofia? | 0.92 | 2 |
| 33 | Which is located in India, University of the Philippines or The Northcap University? | 1.00 | 2 |
| 34 | Eddie Jemison had a role in the television series "IZombie", which premiered on what date? | 1.00 | 4 |
| 35 | What mine was operated by Royal Oak Mines at at earlier date, Kemess Mine or Colomac Mine? | 1.00 | 2 |
| 36 | The Black Star identified closely with this American magazine magnate who was called what? | 1.00 | 2 |
| 37 | What role was played in "Who Framed Roger Rabbit" by the actor who played an Addams Family character played by Jackie Coogan in the original television series? | 0.00 | 2 |
| 38 | Peter Dhao created a websiteto reflect worldwide views. What was the slogan of the site he created ? | 1.00 | 2 |
| 39 | What Nobel Laureate teaches at  Chapman University? | 0.10 | 2 |
| 40 | Which genus is native to more continents, Nothoscordum or Callirhoe? | 1.00 | 2 |
| 41 | The Old Ones are more powerful than which of the mightiest Gods? | 0.14 | 2 |
| 42 | The 2011 FA Community Shield annual football match saw Manchester United win the game 3-2 with goals from Nani and this English professional footballer who played as a center-back? | 1.00 | 2 |
| 43 | Which movie is loosley based off the Brother Grimm's "Iron Henry"? | 0.08 | 2 |
| 44 | Who has won more olympic medals: Angelique Kerber or Amélie Mauresmo? | 0.05 | 2 |
| 45 | What writer worked on both The Ice Cream Man and and a 2007 fantasy comedy loosely based on a Donald Henkel poem? | 1.00 | 2 |
| 46 | The most popular temple in terms of attractions is located in what part of the city? | 0.00 | 2 |
| 47 | Is Ordos City more west than Yangzhong? | 0.00 | 2 |
| 48 | In what year was the soft drink that the Coca-Cola Company designed Red Flash to compete against created? | 1.00 | 2 |
| 49 | Cyrina Fiallo has guest starred on which Michael Jacobs-created sitcom? | 0.00 | 2 |
| 50 | KSCW-DT is part of a duopoly with which virtual channel 12 in Wichita? | 1.00 | 2 |
| 51 | The Swiss immigration referendum, February 2014 is an example of what, which was framed by bilateral treaties between Switzerland and the European Union? | 1.00 | 2 |
| 52 | Who wrote the 2009 American home invasion horror film which Andrea Roth was known for her role in  | 0.57 | 2 |
| 53 | The USS Tortuga was named after the Dry Tortugas, a group of desert coral islets 60 miles west of which city with the motto "One Human Family"? | 1.00 | 2 |
| 54 | The actress that played  Pearl Gallagher on the tv sitcom "Diff'rent Strokes" is also the voice of an animated character that debuted in what year? | 1.00 | 2 |
| 55 | Who built the diesel railcars operated by the publicly owned corporation that provided suburban train, tram and bus services in Adelaide, South Australia starting in July 1994? | 1.00 | 2 |
| 56 | Brendon Urie wrote new perspective after firing which bassist? | 0.00 | 2 |
| 57 | Where was the rapper in 13 Dead Men from? | 0.80 | 2 |
| 58 | What number president was Annie Caputo nominated by to become a member of the Nuclear Regulatory Commission? | 0.00 | 2 |
| 59 | What is the English translation of the name of the novel series which the Four III is the final installment of? | 1.00 | 2 |
| 60 | Carol Kane played the wife of which fictional character on Taxi? | 1.00 | 2 |
| 61 | Abraham Lincoln Neiman and his wife Carrie Marcus Neiman cofounded Neiman Marcus with Carrie's brother Herbert in which American city in 1907? | 1.00 | 2 |
| 62 | Are Jiujiang, Guangdong and Ruzhou located in the same Chinese district? | 1.00 | 2 |
| 63 | Which characters are akin to goblins and were added to a Tilted Mill Entertainment video game in 2009? | 1.00 | 2 |
| 64 | The M104 155mm Projectile was specifically designed to carry about 11.7 pounds of what prototypical substance? | 0.50 | 2 |
| 65 | In what city is the football club that Robin Himmelmann is a goalkeeper for based? | 1.00 | 2 |
| 66 | Who was a pianist, Maro Ajemian or Richard C. Sarafian? | 1.00 | 2 |
| 67 | Which genus of plant is named after a person, Amesiella or Cucurbita? | 1.00 | 2 |
| 68 | How many girls and boys are in the seventeen sibling family featured on Counting On? | 0.13 | 2 |
| 69 | What are the colors of the tricolour flag that was adopted in 1919? | 0.80 | 4 |
| 70 | What year did the prison where William Penn wrote No Cross, No Crown stop being used as a prison? | 1.00 | 2 |
| 71 | what is the group called that Dianne Morgan and Joe Wilkinson a part of in the BBC comedy "Two Episodes of Mash" | 0.00 | 2 |
| 72 | Sian Gibson co-wrote which British sitcom, set around a supermarket and car share scheme? | 1.00 | 2 |
| 73 | Which of the following buildings was designed by SHoP Architects: 247 Cherry or General Motors Building? | 1.00 | 2 |
| 74 | in 1992 Spengler Cup all matches were played at the home arena of what professional Swiss ice hockey club  | 1.00 | 2 |
| 75 | What was the former name of the company which operates Hunterston Terminal? | 1.00 | 2 |
| 76 | Which musician is older, Chantal Claret or Max Green? | 0.00 | 2 |
| 77 | When did an IndyCar race driver drive a Formula 1 car designed by Peter McCool? | 0.06 | 2 |
| 78 | Dorothy Sarnoff's personal client list included what AMerican novelist, who has sold over 800 million copies of her books? | 0.33 | 2 |
| 79 | What type of media does J. T. Petty and Outlast have in common? | 0.50 | 2 |
| 80 | McLaren MP4/11 was driven by what Finnish former professional racing driver | 1.00 | 2 |

## HotpotQA additional questions in `hp-t200` (120 more)

| # | Question | POMDP F1 | Hops |
|---|---|---|---|
| 1 | What is the electric racing series British race car driver Alex Lynn drives for and is owned by Virgin Group? | 0.50 | 2 |
| 2 | What baseball team, part of the ten-school collegiate athletic conference headquartered in Irving, Texas, was coached by Randy Mazey in 2016? | 1.00 | 2 |
| 3 | Thirukkalacherry is a village in which Indian town? | 1.00 | 2 |
| 4 | which league is the 121th season of top-tier competitive football in Switzerland which Ulrich Forte coach FC Zürich in the league  | 1.00 | 2 |
| 5 | Who was involved in the arrest of Dread Pirate Roberts? | 0.80 | 2 |
| 6 | Tyler Redenbach was selected 77th overall by the Phoenix Coyotes in an NHL draft that was held in what city? | 0.67 | 2 |
| 7 | Which band was formed first Killing Joke or Acceptance ? | 1.00 | 2 |
| 8 | Which team did Joe Buck's father broadcast for? | 1.00 | 4 |
| 9 | Are Grant Nicholas and Danny Shirley both American singers? | 1.00 | 2 |
| 10 | What substance is always in a trap to prevent the passage of anything from either direction,  even sewer gases?  | 1.00 | 4 |
| 11 | When was Erik Watts' father born? | 1.00 | 2 |
| 12 | John Douglas Gibson lived his whole life in a suburb of what city? | 0.67 | 2 |
| 13 | In what year was the singer who popularized "I'll Keep the Lovelight Burning" born? | 1.00 | 2 |
| 14 | During the Miss USA 2015, Olivia Jordan of Oklahoma was crowned by which American television host, model, taekwondo coach, and beauty queen who won Miss USA 2014? | 1.00 | 2 |
| 15 | Which sport has been played at the BayArena in Leverkusen, Germany, since 1958? | 1.00 | 2 |
| 16 | What was the home city of the author of the famous novel tracing the life of a male roe deer from his birth onward? | 1.00 | 2 |
| 17 | What company did a man who hired Sioux Falls architect Wallace L. Dow to build a home in Worthing, Minnesota found? | 0.00 | 2 |
| 18 | How many personnel does the Navy that had Gilliam-class atttack transports have on active duty? | 0.33 | 2 |
| 19 | Who was the murderer sent to "Old Smokey" for allegedly commiting "The Crime of the Century"? | 1.00 | 2 |
| 20 | When did the mother of Joseph Ferdinand Leopold of Bavaria die? | 0.50 | 2 |
| 21 | Which British engineering company is best known for its luxury motor cars in the era of British history that covers the brief reign of King Edward VII? | 1.00 | 2 |
| 22 | Have tennis players Françoise Dürr and Mate Pavić both won a doubles title? | 1.00 | 2 |
| 23 | Ashly Burch is known for voicing Aloy in a video game released in what year? | 1.00 | 2 |
| 24 | Was Kanako Momota or Mark Hollis born first? | 0.80 | 2 |
| 25 | What do Park So-yeon and Michael Crafter have in common? | 0.00 | 2 |
| 26 | Along which river is the Kentucky Department of Corrections headquarted? | 0.14 | 4 |
| 27 | Alfred Balk served as the secretary of the Committee on the Employment of Minority Groups in the News Media under which United States Vice President? | 1.00 | 2 |
| 28 | Name three best sellers from Arthur Hailey that were released before Donna Tartt was born. | 0.67 | 2 |
| 29 | What was the previous name of the hotel Bill Cosby recorded his comedy album, For Adults Only, in? | 0.00 | 2 |
| 30 | Josephine de Reszke made her debut in what grand opera? | 1.00 | 2 |
| 31 | In which city is the parent company of Sterlite Industries headquartered? | 1.00 | 2 |
| 32 | Roxie Hart starred the entertainer and comedic actor who had what nickname? | 1.00 | 3 |
| 33 | where was class of warships which ARA "Sarandí" is its fourth and last ship built  | 1.00 | 2 |
| 34 | What three other National forests are administered by the same people who administer the park in which the Art Loeb trail runs through? | 1.00 | 2 |
| 35 | The genus containing lions also contains several poorly known what? | 0.00 | 2 |
| 36 | Do Dillingham Airport and Rafael Hernández Airport both handle civilian (passenger) service? | 1.00 | 2 |
| 37 | 3 Arts Entertainment had at least one coalition with what streaming service, with its 13-episode, 2015 season of a Tina Fey created sitcom? | 0.00 | 2 |
| 38 | Jacques Mathou starred in Delicatessen, the 1991 French movie in the style of which celebrated American animator? | 0.06 | 2 |
| 39 | Meet Market is a 2004 film starring which son of a former prime minister? | 1.00 | 2 |
| 40 | What is the surname of the recorder of "Jupiter (Swallow the Moon)" | 1.00 | 2 |
| 41 | The eastern coast of Ivan Zammit's birth city is located along what body of water?  | 1.00 | 2 |
| 42 | Were both Pam Shriver and Amélie Mauresmo alive in the 1960s? | 1.00 | 2 |
| 43 | What American professional Hawaiian surfer born 18 October 1992 won the Rip Curl Pro Portugal? | 1.00 | 2 |
| 44 | Who has more scope of profession, Brian G. Hutton or Xawery Żuławski? | 0.11 | 2 |
| 45 | Does the drink Quick Fuck have more layers than the drink Ti' Punch? | 0.00 | 2 |
| 46 | What CBS-affiliated station serves Pontotoc County, Oklahoma? | 1.00 | 2 |
| 47 | What job do both Alfred Santell and David Fincher have in common? | 0.67 | 3 |
| 48 | What is the first name of the mother of the artist who interpreted Karla  Bonoff's Tell Me Why ? | 1.00 | 2 |
| 49 | The voice of Homer Simpson also voices what alien character in the television series "The Simpsons"? | 1.00 | 2 |
| 50 | Which breed of dog has origins outside of the United States, Old German Shepherd Dog or Black Mouth Cur? | 1.00 | 2 |
| 51 | Yoann Lemoine, a French video director, has created music videos for Lana Del Rey, Katy Perry, and an orchestral country pop ballad by which top pop artist? | 1.00 | 2 |
| 52 | What is the 2010 census population of the county where Wildcat Brook flows through Jackson? | 1.00 | 2 |
| 53 | What country does Haringey Heartlands and The Mall Wood Green have in common? | 0.00 | 2 |
| 54 | Flowers in the Attick starred which "Mad Men" actress? | 0.80 | 2 |
| 55 | Where was the first governor after the The Missouri Compromise from? | 0.00 | 2 |
| 56 | Which battle, the Battle of Cold Harbor, or the Second Battle of Bull Run, was fought first? | 1.00 | 2 |
| 57 | Nell Williams Plays a younger version of this Character in HBO's Game of thrones that is also in Which fantasy novel Series written by George R.R. Martin? | 1.00 | 2 |
| 58 | Eusebio Valli studied alongside a physician who was the pioneer of what field? | 1.00 | 2 |
| 59 | How many times has the national team Joseph Raich Garriga played for in 1941 participated in FIFA World Cups? | 0.04 | 2 |
| 60 | Which eight-time Academy Award nominee was Tennessee Williams's choice to play a leading role in his play "Clothes for a Summer Hotel"? | 1.00 | 2 |
| 61 | Who were the guns stolen from the HMS ship "Marlin" originally produced for? | 1.00 | 2 |
| 62 | Which Russian figure skating coach was a former competitive ice dancer who competed with Olga Pershankova in 1993? | 1.00 | 2 |
| 63 | In what movie did a Kenyan-Mexican actress, who graduated from Hampshire College, star in in 2015? | 0.00 | 4 |
| 64 |  Still Reigning is a live performance DVD that showcases an album described by Kerrang! as what? | 1.00 | 2 |
| 65 | In what 2 countries did both X-Large and A Bathing Ape have stores? | 1.00 | 2 |
| 66 | Saturn AL-31 is an engine that powers the aircraft produced in what country? | 1.00 | 2 |
| 67 | Yakuza Kiwami is a remake of the first video game in what video game series that is an open world action-adventure beat 'em up video game franchise? | 1.00 | 2 |
| 68 | Who is older, Gabe Saporta or John S. Hall? | 1.00 | 2 |
| 69 | Who programmed a cartridge-based development system made by a company noted for authoring Atari's BASIC? | 1.00 | 2 |
| 70 | which  Indian businessman and politician owns Mabula Game Reserve  | 0.80 | 2 |
| 71 | when was the retired Jamaican sprinter which Richard Thompson is, 0.99 seconds slower than born ? | 0.15 | 2 |
| 72 | Which band was active the longest, Spirit of the West or Big Pig? | 1.00 | 2 |
| 73 | Which is farther north, Wynantskill, New York or Hannaford Brothers Company? | 0.07 | 2 |
| 74 | What are the names of the co-directors of the psychological horror film starring Emily Browning and Elizabeth Banks? | 0.33 | 2 |
| 75 | Which bi-annual British style magazine did  Tim Walker  regularly shoots for | 1.00 | 2 |
| 76 | Were Shadows Over Camelot and Battle Sheep released by the same publisher? | 1.00 | 2 |
| 77 | Were Triumph of the Will and The End of America both made in the same year? | 1.00 | 2 |
| 78 | How many minutes outside of Carson City is the Moonlite BunnyRanch on Moonlight Road? | 0.08 | 2 |
| 79 | JSOC was created on the recommendation of a colonel who served in the Malayan Emergency and what other war? | 0.00 | 2 |
| 80 | The "civic rally cross" was sold alongside what other model sold exclusively in Japan at Honda Verno dealerships?  | 0.40 | 2 |
| 81 | What was the companion piece that Poe's brother published? | 0.00 | 2 |
| 82 | Who has released more studio albums, 10 Years or Edward Sharpe and the Magnetic Zeros? | 1.00 | 2 |
| 83 | What type of product is the sponsor of the Premiership Rugby Sevens SeriesSeries ?  | 0.00 | 2 |
| 84 | What type of engine powered both the Saab 36 and the Avro Vulcan? | 0.86 | 2 |
| 85 | SR connector is based on the connector that is often used for what type of cable? | 0.67 | 2 |
| 86 | Jamie Harris is best known for his role as The Hook-Handed Man in a movie directed by who ? | 1.00 | 2 |
| 87 | Who will conduct the firing cannons in Victoria as part of a musical piece written to celebrate the defeat of Napoleon in Russia? | 0.12 | 2 |
| 88 | Kyle York is the Chief Strategy Officer of a company that was aqured by what corporation in 2016? | 0.67 | 2 |
| 89 | The chicken is a type of dance pattern that is a change of pace of what dance? | 1.00 | 2 |
| 90 | What american singer,had Warren Fu as one of their video directors, and also had to face allegation of illegal marriage with R. Kelly? | 1.00 | 2 |
| 91 | What is the architectural distinction of the hotel whose owner and chief developer is Frank Augustus Miller? | 1.00 | 2 |
| 92 | Which of the office buildings used to staff the White House used to be known as the State, War, and Navy Building? | 1.00 | 2 |
| 93 | From what countries are Gauhar Ali and Iftikhar Ahmed from? | 1.00 | 2 |
| 94 | What is the name of the series who's first season was released on Netflix on September 22, 2016 and stars actor pronounced as John-a-kite? | 0.07 | 2 |
| 95 | What was the first year a scientific journal published by an organization located in the Bronx was published? | 1.00 | 2 |
| 96 | What is the population of the city which  Deryl Dedmon came from  | 0.00 | 4 |
| 97 | In which year did this American rapper and actor, from Cleveland, Ohio, who guest-featured in the album "Excuse My French" first release a mixtape? | 0.00 | 2 |
| 98 | Name the actor who has acted in the film Arrival and who has been nominated for the Academy Award for Best Supporting Actor for the film `The Town' ? | 0.00 | 2 |
| 99 | How many episodes were in the 23rd season of a Fox network show which, in it's twenty-second season, aired it's twenty-first episode which was written by John Frink and directed by Bob Anderson. | 0.67 | 2 |
| 100 |  New Hampshire Northcoast Corporation interchanges cars with which holding company of Class II regional railroads? | 1.00 | 2 |
| 101 | In which city have Gary Ayres and Neil Craig both been head coach of the Crows? | 1.00 | 2 |
| 102 | The Collective for Living Cinema of Lower Manhattan featured work from what filmmaker also known as Denis Kaufman? | 1.00 | 2 |
| 103 | Are Harry Everett Smith and Vladimir Danilevich both from Russia? | 1.00 | 2 |
| 104 | On which continent did Pia Miller make her appearance, in the teen magazine, Dolly? | 0.00 | 4 |
| 105 | The William Ulmer Brewery is located in a neighborhood that is policed by who? | 1.00 | 2 |
| 106 | San Jose Secondary Educational Center, is located on the cost of what sea?  | 1.00 | 2 |
| 107 | What was the nationality and profession of the person responsible for the concept of a dimensionless number in physics and engineering? | 1.00 | 2 |
| 108 | Maryland Jockey Club operates a race track in the largest municipality in which Maryland county? | 0.08 | 4 |
| 109 | What year was the company, who released Forever Kingdom for PlayStation 2, founded? | 1.00 | 2 |
| 110 | When was the second album by Jason Daunt's band released? | 1.00 | 2 |
| 111 | Which  baseball team who represents Texas Tech University in NCAA Division I college baseball is  "The Law" its home stadium | 0.89 | 2 |
| 112 | Which band has more members Music for Dead Birds or The Wolfhounds? | 1.00 | 2 |
| 113 | What surrounding river in a Canadian province was Erin Wall born near? | 1.00 | 2 |
| 114 | What military formation were participated in by both Oscar W. Koch and General George Smith Patton Jr. ? | 1.00 | 2 |
| 115 | What is the middle name of the actor who hosted the24th People's Choice Awards with  Reba McEntire ? | 1.00 | 2 |
| 116 | Yves Apollinaire Pede made sand paintings of which South African anti-apartheid revolutionary?  | 1.00 | 2 |
| 117 | Which character did Tamzin Outhwaite play first: Connie (on "Inside No. 9") or Melanie Owen ("EastEnders")? | 0.00 | 2 |
| 118 | What is the name for what was formerly called Grenier Army Air Field which is located in the two communities of Manchester and Londonberry? | 1.00 | 2 |
| 119 | What scientist as well as a practising Roman Cathloic described the electronic voice phenomena as typically brief, usually the length of a work or short phrase? | 1.00 | 2 |
| 120 | Are Mina Loy and Raymond Carver both British writers? | 1.00 | 2 |

## MS MARCO, `ms-test` (60 questions)

| # | Question | POMDP F1 | Hops |
|---|---|---|---|
| 1 | are vapor cigarettes bad for your lungs | 1.00 | 1 |
| 2 | where are equilibrium receptors located | 0.00 | 1 |
| 3 | what does notary public mean | 0.05 | 1 |
| 4 | what types of cells do seminal vesicles contain? | 0.00 | 1 |
| 5 | where do pumice stones originate | 0.00 | 1 |
| 6 | what is spongiotic dermatitis treatment | 0.15 | 1 |
| 7 | what movie is baymax from | 0.86 | 1 |
| 8 | where does papua new guinea originate | 0.67 | 1 |
| 9 | BOD biological oxygen definition | 0.23 | 1 |
| 10 | how to pronounce sram | 0.00 | 1 |
| 11 | what is barley malt | 0.40 | 1 |
| 12 | what is strategic initiative | 0.12 | 1 |
| 13 | how long can a body be refrigerated before burial | 0.00 | 1 |
| 14 | in what types of cells are chloroplasts found | 0.36 | 1 |
| 15 | what is fme | 0.21 | 1 |
| 16 | what is a phytate | 0.35 | 1 |
| 17 | corrections bc salary | 0.00 | 1 |
| 18 | can baby bunnies have strawberries | 0.00 | 1 |
| 19 | what is echocardiogram test | 0.42 | 1 |
| 20 | rna polymerase uses what as a template to synthesize what | 0.21 | 1 |
| 21 | what kind of software is SAS | 0.00 | 1 |
| 22 | omniscient narrator definition literature | 0.50 | 1 |
| 23 | what does EPNS mean | 0.44 | 1 |
| 24 | how many calories are in a pint of shrimp fried rice | 0.00 | 1 |
| 25 | what does S&M mean | 0.21 | 1 |
| 26 | what is the average pay for police officers vs the army | 0.00 | 1 |
| 27 | is wirra wirra aboriginal | 1.00 | 1 |
| 28 | average summer temperatures in boston | 0.00 | 1 |
| 29 | what is nrf2 activator | 0.09 | 1 |
| 30 | average np salary in texas | 0.00 | 1 |
| 31 | can you have numerous genotype hcv infections | 1.00 | 1 |
| 32 | how do cats help us | 0.62 | 1 |
| 33 | what are exports of sweden | 0.58 | 1 |
| 34 | normal pulse rate in adults | 0.60 | 1 |
| 35 | how much does a navy lieutenant make | 0.27 | 1 |
| 36 | what is another name for skeletal muscle tissue | 0.21 | 1 |
| 37 | how long before eagle eggs hatch | 1.00 | 1 |
| 38 | what is low anion gap in blood work | 0.08 | 1 |
| 39 | is ethanol an element or compound | 1.00 | 1 |
| 40 | how much does a clinical technician make | 0.67 | 2 |
| 41 | what is pmi mip funding fee | 0.25 | 1 |
| 42 | what is a ventilation system | 0.12 | 1 |
| 43 | significance of the golden gate bridge | 0.39 | 1 |
| 44 | what does microscopic urinalysis tell you | 0.17 | 1 |
| 45 | what are the significance of Streptococcus pyogenes | 0.17 | 1 |
| 46 | what is gamification in marketing | 0.12 | 1 |
| 47 | what helps bruises heal quicker | 0.04 | 1 |
| 48 | what is family centred care | 0.57 | 1 |
| 49 | how long does it take to cremate a body | 0.50 | 1 |
| 50 | cleveland is in what county in ohio | 1.00 | 1 |
| 51 | when does implantation in pregnancy occur | 0.60 | 1 |
| 52 | what does landrace mean | 0.62 | 1 |
| 53 | how can the speed of light be used to measure distance | 0.04 | 1 |
| 54 | what is the meaning of atharva veda | 0.00 | 1 |
| 55 | does advantage contain fipronil | 0.00 | 1 |
| 56 | how to handle exception in powershell | 0.04 | 1 |
| 57 | what is cabergoline used for | 0.08 | 1 |
| 58 | how to determine confidence interval in excel | 0.15 | 1 |
| 59 | what does wisteria contamination cause | 0.19 | 1 |
| 60 | col cost of living index | 1.00 | 1 |
