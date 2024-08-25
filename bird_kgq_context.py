# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



# This file contains synthetically created samples for the superhero and the student_club datasets 
# The 15 additional examples were created with Gemini Advanced 

california_schools_kgq = """
Simple Difficulty:

Question: List the names of all schools in Los Angeles County.Evidence: Los Angeles County refers to County Name = 'Los Angeles' in the table frpm
SQL: SELECT School Name FROM frpm WHERE County Name = 'Los Angeles'

Question: What is the total enrollment (K-12) of the school with CDSCode '12345'?Evidence: CDSCode '12345' refers to CDSCode = '12345' in the table frpm
SQL: SELECT Enrollment (K-12) FROM frpm WHERE CDSCode = '12345'

Question: List the cities where schools offer the 'International Baccalaureate' educational option.Evidence: 'International Baccalaureate' is an Educational Option TypeSQL: SELECT DISTINCT City FROM schools WHERE EdOpsName = 'International Baccalaureate'

Question: How many schools have a 'Closed' status type?Evidence: 'Closed' is a StatusTypeSQL: SELECT COUNT(*) FROM schools WHERE StatusType = 'Closed'

Question: What is the average math score for schools in the 'San Francisco Unified' district?Evidence: 'San Francisco Unified' is a District NameSQL: SELECT AVG(AvgScrMath) FROM satscores WHERE dname = 'San Francisco Unified'

Moderate Difficulty:

Question: Among schools with more than 1000 students aged 5-17, what is the average 'Free Meal Count (Ages 5-17)'?Evidence: more than 1000 students aged 5-17 refers to Enrollment (Ages 5-17) > 1000
SQL: SELECT AVG(Free Meal Count (Ages 5-17)) FROM frpm WHERE Enrollment (Ages 5-17) > 1000

Question: List the names and counties of schools that are both 'Charter' and 'Magnet' schools.Evidence: 'Charter' school refers to Charter School (Y/N) = 1; 'Magnet' school refers to Magnet = 1
SQL: SELECT T1.School Name, T1.County FROM frpm AS T1 INNER JOIN schools AS T2 ON T1.CDSCode = T2.CDSCode WHERE T1.Charter School (Y/N) = 1 AND T2.Magnet = 1

Question: What is the total number of test takers in schools located in 'Los Angeles' county that offer the 'Virtual' educational option?Evidence: 'Los Angeles' is a County Name; 'Virtual' educational option refers to Educational Option Type = 'Virtual'
SQL: SELECT SUM(T1.NumTstTakr)
FROM satscores AS T1
INNER JOIN frpm AS T2 ON T1.cds = T2.CDSCode
WHERE T2.County Name = 'Los Angeles'
AND EXISTS (
SELECT 1
FROM schools AS T3
WHERE T3.CDSCode = T2.CDSCode
AND T3.EdOpsName = 'Virtual'
)

Question: List the district names and their average SAT reading scores for districts with more than 5 schools.Evidence: more than 5 schools refers to COUNT(DISTINCT CDSCode) > 5
SQL: SELECT
T1.District Name,
AVG(T2.AvgScrRead) as avg_reading_score
FROM frpm AS T1
INNER JOIN satscores AS T2 ON T1.CDSCode = T2.cds
GROUP BY T1.District Name
HAVING COUNT(DISTINCT T1.CDSCode) > 5

Question:  What is the difference in the average 'FRPM Count (K-12)' between 'Charter' and 'Non-Charter' schools in 'San Diego' county?Evidence: 'Charter' school refers to Charter School (Y/N) = 1; 'Non-Charter' school refers to Charter School (Y/N) = 0; 'San Diego' is a County NameSQL: SELECT
AVG(CASE WHEN Charter School (Y/N) = 1 THEN FRPM Count (K-12) ELSE NULL END) -
AVG(CASE WHEN Charter School (Y/N) = 0 THEN FRPM Count (K-12) ELSE NULL END) AS frm_difference
FROM frpm
WHERE County Name = 'San Diego'

Challenging Difficulty:

Question: Find the top 3 counties with the highest percentage of schools offering 'Career Technical Education' as an educational option.Evidence: 'Career Technical Education' is an Educational Option Type; percentage = (COUNT(schools with 'Career Technical Education') / COUNT(all schools in the county)) * 100
SQL: SELECT
County,
(CAST(SUM(CASE WHEN EdOpsName = 'Career Technical Education' THEN 1 ELSE 0 END) AS REAL) / COUNT(*)) * 100 AS percentage
FROM schools
GROUP BY County
ORDER BY percentage DESC
LIMIT 3

Question: List the school names and their total enrollment for schools that have an average SAT Math score higher than the overall average SAT Math score and are located in cities with a zip code type of 'Standard'.Evidence: overall average SAT Math score refers to AVG(AvgScrMath) from satscores; zip code type of 'Standard' refers to type = 'Standard' in zip_code table
SQL: SELECT
S.School,
F.Enrollment (K-12) + F.Enrollment (Ages 5-17) AS total_enrollment
FROM schools S
JOIN frpm F ON S.CDSCode = F.CDSCode
JOIN satscores SS ON S.CDSCode = SS.cds
JOIN zip_code Z ON S.Zip = Z.zip_code
WHERE SS.AvgScrMath > (SELECT AVG(AvgScrMath) FROM satscores)
AND Z.type = 'Standard'

Question: For each district, find the school with the highest 'FRPM Count (K-12)' and display its name, the district name, and the FRPM count.Evidence: highest 'FRPM Count (K-12)' refers to MAX(FRPM Count (K-12)) for each District NameSQL: SELECT
F.School Name,
F.District Name,
F.FRPM Count (K-12)
FROM frpm F
WHERE F.FRPM Count (K-12) = (
SELECT MAX(FRPM Count (K-12))
FROM frpm F2
WHERE F2.District Name = F.District Name
)

Question: Identify the schools where the difference between the 'FRPM Count (Ages 5-17)' and the 'Free Meal Count (Ages 5-17)' is greater than 100, and list their names along with the corresponding counts.Evidence: difference greater than 100 refers to FRPM Count (Ages 5-17) - Free Meal Count (Ages 5-17) > 100
SQL: SELECT
School Name,FRPM Count (Ages 5-17),Free Meal Count (Ages 5-17)
FROM frpm
WHERE FRPM Count (Ages 5-17) - Free Meal Count (Ages 5-17) > 100

Question: Find the average SAT Math score for schools that were opened before 1990 and have a 'Directly funded' charter funding type.Evidence: opened before 1990 refers to YEAR(OpenDate) < 1990; 'Directly funded' is a Charter Funding TypeSQL: SELECT AVG(T1.AvgScrMath)
FROM satscores AS T1
INNER JOIN frpm AS T2 ON T1.cds = T2.CDSCode
INNER JOIN schools AS T3 ON T2.CDSCode = T3.CDSCode
WHERE strftime('%Y', T3.OpenDate) < '1990'
AND T2.Charter Funding Type = 'Directly funded'
"""


card_games_kgq = """
Simple difficulty

Question: List the names of all cards illustrated by 'Rebecca Guay'.Evidence: 'Rebecca Guay' is an artistSQL: SELECT name FROM cards WHERE artist = 'Rebecca Guay'

Question: How many cards have a 'legendary' frame effect?Evidence: 'legendary' is a frameEffects value.SQL: SELECT COUNT(*) FROM cards WHERE frameEffects = 'legendary'

Question: Find the originalType of the card named 'Lightning Bolt'.Evidence: 'Lightning Bolt' is a name.SQL: SELECT originalType FROM cards WHERE name = 'Lightning Bolt'

Question: List all the unique borderColor values present in the cards table
Evidence: No specific evidence needed, it's about exploring the table
SQL: SELECT DISTINCT borderColor FROM cards

Question:  Find the setCode of all cards that are 'Story Spotlight' cards
Evidence: 'Story Spotlight' cards are indicated by isStorySpotlight = 1
SQL: SELECT setCode FROM cards WHERE isStorySpotlight = 1

Moderate difficulty

Question: List the names of all cards that have a convertedManaCost of 3 and are 'legal' in the 'modern' format
Evidence: 'modern' is a format; 'legal' is a statusSQL: SELECT T1.name
FROM cards AS T1
INNER JOIN legalities AS T2 ON T1.uuid = T2.uuid
WHERE T1.convertedManaCost = 3 AND T2.format = 'modern' AND T2.status = 'Legal'

Question: Find the average edhrecRank of cards with 'showcase' frameEffects.Evidence: 'showcase' is a frameEffects value
SQL: SELECT AVG(edhrecRank) FROM cards WHERE frameEffects = 'showcase'

Question: List the setCode and releaseDate of all sets that have been translated into 'German'.Evidence: 'German' is a languageSQL: SELECT T1.code AS setCode, T1.releaseDate
FROM sets AS T1
INNER JOIN set_translations AS T2 ON T1.code = T2.setCode
WHERE T2.language = 'German'

Question:  Find all cards illustrated by 'Seb McKinnon' and list their name, type, and whether they have a contentWarning (yes/no).Evidence: 'Seb McKinnon' is an artist; contentWarning is indicated by hasContentWarningSQL: SELECT name, type,
CASE WHEN hasContentWarning = 1 THEN 'Yes' ELSE 'No' END AS contentWarning
FROM cards
WHERE artist = 'Seb McKinnon'

Question: List the names of all cards that have a ruling with the text "This is a static ability" and are 'legal' in the 'pioneer' format
Evidence:  'pioneer' is a format; 'legal' is a statusSQL: SELECT c.name
FROM cards c
JOIN rulings r ON c.uuid = r.uuid
JOIN legalities l ON c.uuid = l.uuid
WHERE r.text = 'This is a static ability'
AND l.format = 'pioneer'
AND l.status = 'Legal'

Challenging Difficulty

Question: Find the top 5 artists who have illustrated the most cards that are 'banned' in at least one format
Evidence:  'banned' is a statusSQL: SELECT artist, COUNT(*) as num_banned_cards
FROM cards c
JOIN legalities l ON c.uuid = l.uuid
WHERE l.status = 'Banned'
GROUP BY artist
ORDER BY num_banned_cards DESC
LIMIT 5

Question: For each setCode, calculate the percentage of cards that have a foreign_data entry.Evidence: This requires joining cards and foreign_data and calculating percentages per set
SQL: SELECT
c.setCode,
(CAST(COUNT(f.uuid) AS REAL) / COUNT(*)) * 100 AS percentage_with_foreign_data
FROM cards c
LEFT JOIN foreign_data f ON c.uuid = f.uuid
GROUP BY c.setCode

Question: Find the sets that have at least one card with a convertedManaCost of 10 or higher and are 'legal' in the 'commander' format. List the set name and the number of such cards in each set
Evidence:  'commander' is a format; 'legal' is a statusSQL: SELECT s.name, COUNT(*) as num_high_cost_cards
FROM sets s
JOIN cards c ON s.code = c.setCode
JOIN legalities l ON c.uuid = l.uuid
WHERE c.convertedManaCost >= 10
AND l.format = 'commander'
AND l.status = 'Legal'
GROUP BY s.name

Question: Identify the cards that have rulings related to both 'mana abilities' and 'triggered abilities'. List their names and the corresponding ruling texts
Evidence: This involves searching the rulings.text for specific phrases
SQL: SELECT c.name, r.text
FROM cards c
JOIN rulings r ON c.uuid = r.uuid
WHERE r.text LIKE '%mana ability%'
AND r.text LIKE '%triggered ability%'

Question:  Find the sets that have the highest percentage of cards with 'showcase' frameEffects. List the set name and the percentage
Evidence:  'showcase' is a frameEffects value
SQL: SELECT
s.name,
(CAST(SUM(CASE WHEN c.frameEffects = 'showcase' THEN 1 ELSE 0 END) AS REAL) / COUNT(*)) * 100 AS showcase_percentage
FROM sets s
JOIN cards c ON s.code = c.setCode
GROUP BY s.name
ORDER BY showcase_percentage DESC
LIMIT 1
"""


codebase_community_kgq = """
Simple Difficulty

Question: List the display names of all users who have the 'Fanatic' badge.Evidence: 'Fanatic' is a value in the Name column of the badges table.SQL: SELECT u.DisplayName
FROM users u
JOIN badges b ON u.Id = b.UserId
WHERE b.Name = 'Fanatic'

Question: What is the location of the user with the highest reputation?Evidence: Highest reputation refers to the maximum value in the Reputation column of the users table.SQL: SELECT Location
FROM users
WHERE Reputation = (SELECT MAX(Reputation) FROM users)

Question:  How many posts have a score greater than 50?Evidence: A score greater than 50 refers to Score > 50 in the posts table
SQL: SELECT COUNT(*) FROM posts WHERE Score > 50

Question: Find the creation date of the post with ID 12345
Evidence: Post with ID 12345 refers to Id = 12345 in the posts table
SQL: SELECT CreationDate FROM posts WHERE Id = 12345

Question: List the tag names that have been used more than 100 times
Evidence: Used more than 100 times refers to Count > 100 in the tags table
SQL: SELECT TagName FROM tags WHERE Count > 100

Moderate Difficulty

Question:  Find the average age of users who have the 'Electorate' badge
Evidence: 'Electorate' is a value in the Name column of the badges table.SQL: SELECT AVG(u.Age)
FROM users u
JOIN badges b ON u.Id = b.UserId
WHERE b.Name = 'Electorate'

Question: List the titles of the top 3 posts with the highest ViewCount.Evidence: Top 3 posts with the highest ViewCount means ordering by ViewCount in descending order and limiting the results to 3
SQL: SELECT Title FROM posts ORDER BY ViewCount DESC LIMIT 3;

Question:  Find the display names of users who have both 'Teacher' and 'Student' badges.Evidence: 'Teacher' and 'Student' are values in the Name column of badges table
SQL: SELECT u.DisplayName
FROM users u
WHERE EXISTS (
SELECT 1 FROM badges b
WHERE b.UserId = u.Id AND b.Name = 'Teacher'
)
AND EXISTS (
SELECT 1 FROM badges b
WHERE b.UserId = u.Id AND b.Name = 'Student'
)

Question: For each Location, calculate the average reputation of users from that location
Evidence: This requires grouping by Location and calculating the average of ReputationSQL: SELECT Location, AVG(Reputation) as avg_reputation
FROM users
GROUP BY Location

Question: List the titles and scores of posts that have more than 5 comments and were last edited by a user with reputation higher than 1000.Evidence: More than 5 comments refers to CommentCount > 5; reputation higher than 1000 refers to Reputation > 1000
SQL: SELECT p.Title, p.Score
FROM posts p
JOIN users u ON p.LastEditorUserId = u.Id
WHERE p.CommentCount > 5 AND u.Reputation > 1000

Challenging Difficulty

Question: Find the users who have voted on at least 3 different posts that have the tag 'machine-learning'. List their display names.Evidence: 'machine-learning' is a TagName; at least 3 different posts requires counting distinct PostIds
SQL: SELECT u.DisplayName
FROM users u
JOIN votes v ON u.Id = v.UserId
JOIN posts p ON v.PostId = p.Id
JOIN tags t ON p.Id = t.ExcerptPostId
WHERE t.TagName = 'machine-learning'
GROUP BY u.Id
HAVING COUNT(DISTINCT v.PostId) >= 3

Question:  For each year, calculate the average number of badges earned by users who created their accounts in that year
Evidence: This requires joining users and badges, grouping by year of CreationDate and calculating averages
SQL: SELECT
strftime('%Y', u.CreationDate) AS year,
AVG(badge_count) AS avg_badges
FROM users u
JOIN (
SELECT UserId, COUNT(*) as badge_count
FROM badges
GROUP BY UserId
) b ON u.Id = b.UserId
GROUP BY year

Question: Find the posts that have been edited at least twice and have an average comment score higher than 5. List their titles and the number of times they have been edited
Evidence: Edited at least twice implies counting the number of PostHistory entries for each PostId; average comment score requires joining with comments and calculating the average
SQL: SELECT
p.Title,
COUNT(ph.Id) - 1 AS edit_count
FROM posts p
JOIN postHistory ph ON p.Id = ph.PostId
JOIN comments c ON p.Id = c.PostId
GROUP BY p.Id, p.Title
HAVING COUNT(ph.Id) > 2
AND AVG(c.Score) > 5

Question: Identify the users who have earned all three badges: 'Teacher', 'Student', and 'Editor'. List their display names
Evidence: This requires ensuring a user has all three specific badges
SQL: SELECT u.DisplayName
FROM users u
WHERE EXISTS (
SELECT 1 FROM badges b
WHERE b.UserId = u.Id AND b.Name = 'Teacher'
)
AND EXISTS (
SELECT 1 FROM badges b
WHERE b.UserId = u.Id AND b.Name = 'Student'
)
AND EXISTS (
SELECT 1 FROM badges b
WHERE b.UserId = u.Id AND b.Name = 'Editor'
)

Question:  For each post with at least one comment, find the comment with the highest score and display the post title, comment text, and the commenter's display name
Evidence: This requires joining posts and comments, grouping by PostId, and finding the maximum Score within each group
SQL: SELECT
p.Title,
c.Text AS comment_text,
u.DisplayName AS commenter_name
FROM posts p
JOIN comments c ON p.Id = c.PostId
JOIN users u ON c.UserId = u.Id
WHERE p.CommentCount > 0
AND c.Score = (
SELECT MAX(Score)
FROM comments c2
WHERE c2.PostId = p.Id
)
"""


debit_card_specializing_kgq = """
Simple Difficulty

Question: List the segments of customers who pay in EUR.Evidence: Currency = 'EUR'
SQL: SELECT DISTINCT Segment FROM customers WHERE Currency = 'EUR'

Question: What is the total consumption of customer with ID 3 in the year 2013?Evidence: CustomerID = 3; Year 2013 can be represented as Date BETWEEN 201301 AND 201312
SQL: SELECT SUM(Consumption) FROM yearmonth WHERE CustomerID = 3 AND Date BETWEEN 201301 AND 201312

Question: List the countries where 'Premium' gas stations are located.Evidence: 'Premium' is a Segment in the gasstations table
SQL: SELECT DISTINCT Country FROM gasstations WHERE Segment = 'Premium'

Question:  Find the total number of transactions made in 'Slovakia'.Evidence: 'Slovakia' is represented by Country = 'SVK' in the gasstations table
SQL: SELECT COUNT(*)
FROM transactions_1k t
JOIN gasstations g ON t.GasStationID = g.GasStationID
WHERE g.Country = 'SVK'

Question:  List the distinct product IDs purchased by customers in the 'LAM' segment
Evidence: 'LAM' is a Segment in the customers table
SQL: SELECT DISTINCT t.ProductID
FROM transactions_1k t
JOIN customers c ON t.CustomerID = c.CustomerID
WHERE c.Segment = 'LAM'

Moderate Difficulty

Question: What is the average consumption in 2011 for customers who pay in CZK?Evidence: Year 2011 can be represented as Date BETWEEN 201101 AND 201112; Currency = 'CZK'; average consumption refers to AVG(Consumption)
SQL: SELECT AVG(ym.Consumption)
FROM yearmonth ym
JOIN customers c ON ym.CustomerID = c.CustomerID
WHERE c.Currency = 'CZK' AND ym.Date BETWEEN 201101 AND 201112

Question: List the GasStationID and total amount spent for transactions made by customers in the 'SME' segment in the year 2013
Evidence: 'SME' is a Segment in the customers table; Year 2013 can be represented as Date LIKE '2013%' in the transactions_1k table; total amount spent refers to SUM(Price)
SQL: SELECT
t.GasStationID,
SUM(t.Price) AS total_spent
FROM transactions_1k t
JOIN customers c ON t.CustomerID = c.CustomerID
WHERE c.Segment = 'SME' AND t.Date LIKE '2013%'
GROUP BY t.GasStationID

Question: Find the month and year with the highest average consumption for customers in the 'KAM' segment
Evidence: 'KAM' is a Segment in the customers table; highest average consumption refers to MAX(AVG(Consumption)); month and year can be extracted from DateSQL: SELECT
SUBSTR(ym.Date, 1, 4) AS year,
SUBSTR(ym.Date, 5, 2) AS month,
AVG(ym.Consumption) as avg_consumption
FROM yearmonth ym
JOIN customers c ON ym.CustomerID = c.CustomerID
WHERE c.Segment = 'KAM'
GROUP BY year, month
ORDER BY avg_consumption DESC
LIMIT 1

Question:  List the product descriptions and their average price per unit, for products purchased more than 5 times
Evidence: average price per unit is calculated as Price / Amount; purchased more than 5 times means COUNT() > 5
SQL: SELECT
p.Description,
AVG(t.Price / t.Amount) AS avg_price_per_unit
FROM transactions_1k t
JOIN products p ON t.ProductID = p.ProductID
GROUP BY p.Description
HAVING COUNT() > 5

Question:  Find the difference in the total number of 'Discount' and 'Premium' gas stations in each country
Evidence: 'Discount' and 'Premium' are Segment values in the gasstations table; difference is calculated using SUM(CASE WHEN ... )
SQL: SELECT
Country,
SUM(CASE WHEN Segment = 'Discount' THEN 1 ELSE 0 END) -
SUM(CASE WHEN Segment = 'Premium' THEN 1 ELSE 0 END) AS segment_difference
FROM gasstations
GROUP BY Country

Challenging Difficulty

Question: For each customer segment, find the year with the highest total consumption and the corresponding consumption value
Evidence: highest total consumption refers to MAX(SUM(Consumption)) for each Segment and year; year can be extracted from DateSQL: SELECT
c.Segment,
SUBSTR(ym.Date, 1, 4) AS year,
SUM(ym.Consumption) as total_consumption
FROM customers c
JOIN yearmonth ym ON c.CustomerID = ym.CustomerID
GROUP BY c.Segment, year
HAVING SUM(ym.Consumption) = (
SELECT MAX(total_consumption)
FROM (
SELECT SUM(Consumption) as total_consumption
FROM yearmonth ym2
WHERE ym2.CustomerID = ym.CustomerID
GROUP BY SUBSTR(ym2.Date, 1, 4)
)
)

Question: Identify the top 3 months in 2013 where the total transaction amount across all customers was the highest. Show the month, year, and the total amount
Evidence: top 3 months refers to the top 3 Date values with the highest SUM(Amount); month and year can be extracted from DateSQL: SELECT
SUBSTR(Date, 1, 4) AS year,
SUBSTR(Date, 5, 2) AS month,
SUM(Amount) as total_amount
FROM transactions_1k
WHERE Date LIKE '2013%'
GROUP BY year, month
ORDER BY total_amount DESC
LIMIT 3

Question: Find the customer IDs who made transactions at both 'Discount' and 'Premium' gas stations in the same month of 2012.Evidence: 'Discount' and 'Premium' are Segment values in gasstations; same month requires grouping by month extracted from Date and ensuring COUNT(DISTINCT Segment) = 2
SQL: SELECT t.CustomerID
FROM transactions_1k t
JOIN gasstations g ON t.GasStationID = g.GasStationID
WHERE t.Date LIKE '2012%'
GROUP BY t.CustomerID, SUBSTR(t.Date, 5, 2)
HAVING COUNT(DISTINCT g.Segment) = 2
AND 'Discount' IN (SELECT g2.Segment FROM gasstations g2 WHERE g2.GasStationID = t.GasStationID)
AND 'Premium' IN (SELECT g2.Segment FROM gasstations g2 WHERE g2.GasStationID = t.GasStationID)

Question: Calculate the average consumption for each CustomerID in 2013, and then find the median of these average consumptions
Evidence: average consumption for each CustomerID is AVG(Consumption); median requires using a subquery and percentile function
SQL: SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY avg_consumption) AS median_consumption
FROM (
SELECT CustomerID, AVG(Consumption) as avg_consumption
FROM yearmonth
WHERE Date BETWEEN 201301 AND 201312
GROUP BY CustomerID
)

Question:  Identify the gas station chains that have at least one gas station in each of the three countries: 'CZE', 'SVK', and 'POL'. List the chain IDs
Evidence: 'CZE', 'SVK', and 'POL' are Country values; requires ensuring a ChainID has entries for all three countries
SQL: SELECT ChainID
FROM gasstations
WHERE Country IN ('CZE', 'SVK', 'POL')
GROUP BY ChainID
HAVING COUNT(DISTINCT Country) = 3
"""


financial_kgq = """
Simple Difficulty

Question: List the district names in the 'Central Bohemia' region
Evidence: 'Central Bohemia' is a value in the A3 column of the district table
SQL: SELECT A2 FROM district WHERE A3 = 'Central Bohemia'

Question: How many clients have a birth date before '1960-01-01'?Evidence: Birth date before '1960-01-01' refers to birth_date < '1960-01-01' in the client table
SQL: SELECT COUNT(*) FROM client WHERE birth_date < '1960-01-01'

Question: Find the average balance of all transactions in the year 1995
Evidence: Transactions in the year 1995 refers to date LIKE '1995%' in the trans table; average balance refers to AVG(balance)
SQL: SELECT AVG(balance) FROM trans WHERE date LIKE '1995%'

Question: List the distinct account frequencies used by clients
Evidence: Account frequencies are stored in the frequency column of the account table
SQL: SELECT DISTINCT frequency FROM account

Question:  Find the total number of loans approved in the year 1998
Evidence: Loans approved in the year 1998 refers to date LIKE '1998%' in the loan table
SQL: SELECT COUNT(*) FROM loan WHERE date LIKE '1998%'

Moderate Difficulty

Question: What is the average loan duration for loans approved in the 'South Moravia' region?Evidence: 'South Moravia' is a value in the A3 column of the district table; loan duration is in the duration column of the loan table
SQL: SELECT AVG(l.duration)
FROM loan l
JOIN account a ON l.account_id = a.account_id
JOIN district d ON a.district_id = d.district_id
WHERE d.A3 = 'South Moravia'

Question: List the account IDs and their opening dates for accounts that have a balance greater than 5000 in any transaction
Evidence: Balance greater than 5000 refers to balance > 5000 in the trans table
SQL: SELECT DISTINCT t.account_id, a.date
FROM trans t
JOIN account a ON t.account_id = a.account_id
WHERE t.balance > 5000

Question:  Find the districts with the highest and lowest average salary. Show the district name and the average salary
Evidence: Average salary is in the A11 column of district; highest and lowest refer to MAX(A11) and MIN(A11)
SQL: SELECT A2 as district_name, A11 as avg_salary
FROM district
WHERE A11 = (SELECT MAX(A11) FROM district)
OR A11 = (SELECT MIN(A11) FROM district)

Question: List the client IDs and their birth dates who have made at least one 'VYBER KARTOU' (credit card withdrawal) transaction
Evidence: 'VYBER KARTOU' is an operation in the trans table
SQL: SELECT DISTINCT c.client_id, c.birth_date
FROM client c
JOIN disp d ON c.client_id = d.client_id
JOIN account a ON d.account_id = a.account_id
JOIN trans t ON a.account_id = t.account_id
WHERE t.operation = 'VYBER KARTOU'

Question:  Calculate the total amount of loans approved for each gender in the year 1996
Evidence: Loans approved in the year 1996 refers to date LIKE '1996%' in the loan table; total amount of loans refers to SUM(amount)
SQL: SELECT
c.gender,
SUM(l.amount) AS total_loan_amount
FROM client c
JOIN disp d ON c.client_id = d.client_id
JOIN account a ON d.account_id = a.account_id
JOIN loan l ON a.account_id = l.account_id
WHERE l.date LIKE '1996%'
GROUP BY c.gender

Challenging Difficulty

Question:  Find the districts where the average loan amount for 'Male' clients is higher than the average loan amount for 'Female' clients.Evidence: Average loan amount needs to be calculated separately for each gender and compared; 'Male' and 'Female' are values in the gender column
SQL: SELECT d.A2 as district_name
FROM district d
WHERE (
SELECT AVG(l.amount)
FROM loan l
JOIN account a ON l.account_id = a.account_id
JOIN disp di ON a.account_id = di.account_id
JOIN client cl ON di.client_id = cl.client_id
WHERE d.district_id = a.district_id
AND cl.gender = 'M'
) > (
SELECT AVG(l.amount)
FROM loan l
JOIN account a ON l.account_id = a.account_id
JOIN disp di ON a.account_id = di.account_id
JOIN client cl ON di.client_id = cl.client_id
WHERE d.district_id = a.district_id
AND cl.gender = 'F'
)

Question: Identify the top 3 districts with the highest ratio of 'OWNER' type dispositions to the total number of dispositions
Evidence: Ratio calculation involves COUNT with conditions; 'OWNER' is a type in the disp table
SQL: SELECT
d.A2 AS district_name,
(CAST(SUM(CASE WHEN di.type = 'OWNER' THEN 1 ELSE 0 END) AS REAL) / COUNT(*)) * 100 AS owner_percentage
FROM district d
JOIN account a ON d.district_id = a.district_id
JOIN disp di ON a.account_id = di.account_id
GROUP BY d.A2
ORDER BY owner_percentage DESC
LIMIT 3

Question:  For each year between 1993 and 1998, calculate the total amount withdrawn ('VYDAJ') using credit cards ('VYBER KARTOU')
Evidence: 'VYDAJ' and 'VYBER KARTOU' are type and operation values in the trans table respectively
SQL: SELECT
strftime('%Y', date) as year,
SUM(amount) as total_withdrawal
FROM trans
WHERE operation = 'VYBER KARTOU' AND type = 'VYDAJ'
AND strftime('%Y', date) BETWEEN '1993' AND '1998'
GROUP BY year

Question: Find the clients who have made transactions at more than 3 different gas stations. List their client IDs
Evidence: This requires joining transactions_1k and gasstations, grouping by CustomerID and counting distinct GasStationIDs
SQL: SELECT CustomerID
FROM transactions_1k
GROUP BY CustomerID
HAVING COUNT(DISTINCT GasStationID) > 3

Question: Identify the 'Card ID' that has been used for the highest total transaction amount in 'Premium' gas stations located in 'Slovakia'
Evidence: 'Premium' is a Segment in gasstations; 'Slovakia' is represented by Country = 'SVK'; highest total transaction amount refers to MAX(SUM(Amount))
SQL: SELECT t.CardID
FROM transactions_1k t
JOIN gasstations g ON t.GasStationID = g.GasStationID
WHERE g.Segment = 'Premium' AND g.Country = 'SVK'
GROUP BY t.CardID
ORDER BY SUM(t.Amount) DESC
LIMIT 1
"""

toxicology_kgq = """
Simple Difficulty:

Question: List the molecule IDs of all molecules containing the element 'Fe' (iron).Evidence: iron refers to element = 'Fe'
SQL: SELECT DISTINCT molecule_id FROM atom WHERE element = 'Fe'

Question: How many molecules have a label of '+' (carcinogenic)?Evidence: carcinogenic refers to label = '+'
SQL: SELECT COUNT(*) FROM molecule WHERE label = '+'

Question: List the bond IDs of all bonds in molecule TR050.Evidence: molecule TR050 refers to molecule_id = 'TR050'
SQL: SELECT bond_id FROM bond WHERE molecule_id = 'TR050'

Question: Find the number of atoms in the molecule with the highest number of atoms.Evidence: highest number of atoms refers to MAX(COUNT(atom_id))
SQL: SELECT COUNT(atom_id)
FROM atom
GROUP BY molecule_id
ORDER BY COUNT(atom_id) DESC
LIMIT 1

Question: Are there any molecules with the element 'Au' (gold) that are non-carcinogenic?Evidence: gold refers to element = 'Au'; non-carcinogenic refers to label = '-'
SQL: SELECT COUNT(DISTINCT m.molecule_id)
FROM molecule m
JOIN atom a ON m.molecule_id = a.molecule_id
WHERE a.element = 'Au' AND m.label = '-'

Moderate Difficulty:

Question: What is the average number of atoms in molecules that have at least one triple bond?Evidence: triple bond refers to bond_type = '#'; average number of atoms refers to AVG(COUNT(atom_id))
SQL: SELECT AVG(atom_count)
FROM (
SELECT molecule_id, COUNT(*) as atom_count
FROM atom
WHERE molecule_id IN (
SELECT DISTINCT molecule_id
FROM bond
WHERE bond_type = '#'
)
GROUP BY molecule_id
)

Question: List the molecule IDs and their labels for molecules that contain both 'C' (carbon) and 'O' (oxygen) atoms.Evidence: carbon refers to element = 'C'; oxygen refers to element = 'O'
SQL: SELECT m.molecule_id, m.label
FROM molecule m
WHERE EXISTS (
SELECT 1 FROM atom a
WHERE a.molecule_id = m.molecule_id AND a.element = 'C'
)
AND EXISTS (
SELECT 1 FROM atom a
WHERE a.molecule_id = m.molecule_id AND a.element = 'O'
)

Question: Find the bond types and the count of each bond type for the molecule 'TR085'.Evidence: molecule 'TR085' refers to molecule_id = 'TR085'
SQL: SELECT bond_type, COUNT(*) as bond_count
FROM bond
WHERE molecule_id = 'TR085'
GROUP BY bond_type

Question: List the molecule IDs that have more 'H' (hydrogen) atoms than 'C' (carbon) atoms
Evidence: hydrogen refers to element = 'H'; carbon refers to element = 'C'
SQL: SELECT molecule_id
FROM atom
WHERE element IN ('H', 'C')
GROUP BY molecule_id
HAVING SUM(CASE WHEN element = 'H' THEN 1 ELSE 0 END) >
SUM(CASE WHEN element = 'C' THEN 1 ELSE 0 END)

Question: Are there any atoms that are connected by more than one bond? If yes, list those atom IDs
Evidence: connected by more than one bond means COUNT(bond_id) > 1
SQL: SELECT atom_id
FROM connected
GROUP BY atom_id
HAVING COUNT(bond_id) > 1

Challenging Difficulty

Question: Find the molecules that have at least two different types of bonds. List their molecule IDs and labels
Evidence: at least two different types of bonds requires counting distinct bond_types
SQL: SELECT m.molecule_id, m.label
FROM molecule m
JOIN bond b ON m.molecule_id = b.molecule_id
GROUP BY m.molecule_id, m.label
HAVING COUNT(DISTINCT b.bond_type) >= 2

Question:  Calculate the percentage of non-carcinogenic molecules that contain at least one 'Cl' (chlorine) atom
Evidence: non-carcinogenic refers to label = '-'; chlorine refers to element = 'Cl'; percentage calculation
SQL: SELECT
(CAST(COUNT(DISTINCT m.molecule_id) AS REAL) /
(SELECT COUNT(*) FROM molecule WHERE label = '-')) * 100 AS percentage
FROM molecule m
JOIN atom a ON m.molecule_id = a.molecule_id
WHERE m.label = '-' AND a.element = 'Cl'

Question: For each bond type, find the average number of 'O' (oxygen) atoms present in molecules with that bond type
Evidence: average number of 'O' atoms refers to AVG(COUNT(atom_id) WHERE element = 'O') for each bond_typeSQL: SELECT
b.bond_type,
AVG(oxygen_count) AS avg_oxygen_atoms
FROM bond b
JOIN (
SELECT molecule_id, COUNT(*) AS oxygen_count
FROM atom
WHERE element = 'O'
GROUP BY molecule_id
) o ON b.molecule_id = o.molecule_id
GROUP BY b.bond_type

Question: Identify the molecules where all the atoms involved in bonds are of the same element type. List the molecule IDs
Evidence: This requires careful joining and grouping to ensure all connected atoms have the same element
SQL: SELECT c.molecule_id
FROM connected c
JOIN atom a1 ON c.atom_id = a1.atom_id
JOIN atom a2 ON c.atom_id2 = a2.atom_id
GROUP BY c.molecule_id
HAVING COUNT(DISTINCT a1.element) = 1
AND COUNT(DISTINCT a2.element) = 1
AND a1.element = a2.element

Question: Find the molecules that have exactly 3 'C' (carbon) atoms and at least 2 'H' (hydrogen) atoms. List their molecule IDs and labels
Evidence: exactly 3 'C' atoms and at least 2 'H' atoms involves conditional counting within each molecule
SQL: SELECT m.molecule_id, m.label
FROM molecule m
JOIN atom a ON m.molecule_id = a.molecule_id
WHERE a.element IN ('C', 'H')
GROUP BY m.molecule_id, m.label
HAVING SUM(CASE WHEN a.element = 'C' THEN 1 ELSE 0 END) = 3
AND SUM(CASE WHEN a.element = 'H' THEN 1 ELSE 0 END) >= 2
"""

european_football_2_kgq = """
Simple Difficulty

Question: List the names of all players who have a potential rating greater than 85.Evidence:  potential rating greater than 85 refers to potential > 85
SQL: SELECT player_name
FROM Player
WHERE player_api_id IN (
SELECT player_api_id
FROM Player_Attributes
WHERE potential > 85
)

Question:  What is the average overall rating of players in the 'England Premier League'?Evidence: 'England Premier League' is a value in the name column of the League table; average overall rating refers to AVG(overall_rating)
SQL: SELECT AVG(pa.overall_rating)
FROM Player_Attributes pa
JOIN Match m ON pa.player_api_id = m.home_player_1 -- Assuming home_player_1 is representative
JOIN League l ON m.league_id = l.id
WHERE l.name = 'England Premier League'

Question: Find the team with the lowest buildUpPlaySpeedEvidence: Lowest buildUpPlaySpeed refers to the minimum value in that column
SQL: SELECT t.team_long_name
FROM Team t
JOIN Team_Attributes ta ON t.team_api_id = ta.team_api_id
ORDER BY ta.buildUpPlaySpeed ASC
LIMIT 1

Question: List the countries where matches were played in the '2013/2014' season.Evidence: '2013/2014' is a season value
SQL: SELECT DISTINCT c.name
FROM Country c
JOIN Match m ON c.id = m.country_id
WHERE m.season = '2013/2014'

Question:  Find the number of players whose preferred foot is 'right'.Evidence: 'right' is a value in the preferred_foot column of the Player_Attributes table
SQL: SELECT COUNT(*)
FROM Player_Attributes
WHERE preferred_foot = 'right'

Moderate Difficulty

Question: What is the average gk_reflexes score for players who have an overall_rating above 80?Evidence: overall_rating above 80 refers to overall_rating > 80
SQL: SELECT AVG(gk_reflexes)
FROM Player_Attributes
WHERE overall_rating > 80

Question:  List the names of the top 5 players with the highest shot_power who were born after '1990-01-01'
Evidence: shot_power is a column in Player_Attributes; born after '1990-01-01' refers to birthday > '1990-01-01'
SQL: SELECT p.player_name
FROM Player p
JOIN Player_Attributes pa ON p.player_api_id = pa.player_api_id
WHERE p.birthday > '1990-01-01'
ORDER BY pa.shot_power DESC
LIMIT 5

Question: Find the total number of goals scored in matches played in the 'Spain LIGA BBVA' in the '2011/2012' season
Evidence: 'Spain LIGA BBVA' is a name in the League table; '2011/2012' is a season value; total number of goals is calculated by summing home_team_goal and away_team_goalSQL: SELECT SUM(m.home_team_goal + m.away_team_goal) as total_goals
FROM Match m
JOIN League l ON m.league_id = l.id
WHERE l.name = 'Spain LIGA BBVA' AND m.season = '2011/2012'

Question: List the team_long_name and their average buildUpPlaySpeed for teams that have a 'Balanced' buildUpPlayStyle.Evidence: 'Balanced' is a value in the buildUpPlayStyle column
SQL: SELECT
t.team_long_name,
AVG(ta.buildUpPlaySpeed) as avg_speed
FROM Team t
JOIN Team_Attributes ta ON t.team_api_id = ta.team_api_id
WHERE ta.buildUpPlayStyle = 'Balanced'
GROUP BY t.team_long_name

Question: Find the average age of players who have played in the 'France Ligue 1' and have a potential rating higher than 80.Evidence: 'France Ligue 1' is a name in the League table; potential rating higher than 80 refers to potential > 80; player's age needs to be calculated based on their birthdaySQL: SELECT AVG(CAST ((JULIAN_DAY('now') - JULIAN_DAY(p.birthday)) / 365 AS INTEGER)) as avg_age
FROM Player p
JOIN Player_Attributes pa ON p.player_api_id = pa.player_api_id
JOIN Match m ON p.player_api_id = m.home_player_1 -- Assuming home_player_1 is representative
JOIN League l ON m.league_id = l.id
WHERE l.name = 'France Ligue 1' AND pa.potential > 80

Challenging Difficulty

Question: Find the top 3 countries with the highest average overall_rating of their players in the year 2015
Evidence: This requires joining multiple tables, filtering by year, grouping by country, and calculating averages
SQL: SELECT
c.name AS country_name,
AVG(pa.overall_rating) AS avg_overall_rating
FROM Country c
JOIN Match m ON c.id = m.country_id
JOIN Player_Attributes pa ON m.home_player_1 = pa.player_api_id  -- Assuming home_player_1 is representative
WHERE strftime('%Y', pa.date) = '2015'
GROUP BY c.name
ORDER BY avg_overall_rating DESC
LIMIT 3

Question: Identify the teams that have won all their home matches in the '2012/2013' season. List their long names
Evidence: Won all home matches implies home_team_goal > away_team_goal for all matches of that team in that season
SQL: SELECT t.team_long_name
FROM Team t
WHERE NOT EXISTS (
SELECT 1
FROM Match m
WHERE m.home_team_api_id = t.team_api_id
AND m.season = '2012/2013'
AND m.home_team_goal <= m.away_team_goal
)

Question: For each league, find the player with the highest dribbling score in the '2014/2015' season. Show the league name, player name, and the dribbling score
Evidence: Highest dribbling score requires finding the MAX(dribbling) for each league_id and season
SQL: SELECT
l.name AS league_name,
p.player_name,
pa.dribbling AS dribbling_score
FROM League l
JOIN Match m ON l.id = m.league_id
JOIN Player_Attributes pa ON m.home_player_1 = pa.player_api_id -- Assuming home_player_1 is representative
JOIN Player p ON pa.player_api_id = p.player_api_id
WHERE m.season = '2014/2015'
AND pa.dribbling = (
SELECT MAX(dribbling)
FROM Player_Attributes pa2
JOIN Match m2 ON pa2.player_api_id = m2.home_player_1
WHERE m2.league_id = m.league_id
AND m2.season = m.season
)

Question: Calculate the average overall_rating for each preferred_foot in each league for the '2010/2011' season.Evidence: This requires joining multiple tables, grouping, and calculating averages
SQL: SELECT
l.name AS league_name,
pa.preferred_foot,
AVG(pa.overall
"""

formula_1_kgq = """
Simple Difficulty

Question: List the names of all circuits located in 'Brazil'.Evidence: 'Brazil' is a value in the country column of the circuits table.SQL: SELECT name FROM circuits WHERE country = 'Brazil'

Question:  What is the nationality of the driver with driverId 10?Evidence:  driverId 10 refers to driverId = 10 in the drivers table
SQL: SELECT nationality FROM drivers WHERE driverId = 10

Question: Find the total number of races in the '2015' season
Evidence: '2015' is a value that can be extracted from the date column in the races table
SQL: SELECT COUNT(*) FROM races WHERE strftime('%Y', date) = '2015'

Question: List the distinct statusId values present in the results table
Evidence: No specific evidence needed, it's about exploring the table
SQL: SELECT DISTINCT statusId FROM results

Question: Find the constructorId that won the race with raceId 500
Evidence: Won the race implies positionOrder = 1 in the results table
SQL: SELECT constructorId FROM results WHERE raceId = 500 AND positionOrder = 1

Moderate Difficulty

Question: List the names of circuits that have hosted more than 10 races
Evidence: Hosted more than 10 races requires counting the number of races per circuit using circuitIdSQL: SELECT c.name
FROM circuits c
JOIN races r ON c.circuitId = r.circuitId
GROUP BY c.circuitId, c.name
HAVING COUNT(*) > 10

Question: Find the average overall_rating of drivers who have a preferred_foot of 'left'
Evidence: 'left' is a value in the preferred_foot column
SQL: SELECT AVG(overall_rating)
FROM Player_Attributes
WHERE preferred_foot = 'left'

Question: List the driverRef and their fastest lap time (fastestLapTime) in the 'Monaco Grand Prix' in the year 2013
Evidence: 'Monaco Grand Prix' is a name in races; 2013 can be extracted from the date column
SQL: SELECT
d.driverRef,
r.fastestLapTime
FROM results r
JOIN drivers d ON r.driverId = d.driverId
JOIN races ra ON r.raceId = ra.raceId
WHERE ra.name = 'Monaco Grand Prix' AND strftime('%Y', ra.date) = '2013'
AND r.fastestLapTime IS NOT NULL

Question: For each constructorId, calculate the total number of points they scored in all races.Evidence: Total points requires summing the points column in the constructorStandings table
SQL: SELECT constructorId, SUM(points) as total_points
FROM constructorStandings
GROUP BY constructorId

Question: List the names of drivers who have finished in the top 3 positions ('positionOrder') in at least one race in the '2011' season
Evidence: Top 3 positions means positionOrder <= 3; '2011' can be extracted from the date column
SQL: SELECT DISTINCT d.forename || ' ' || d.surname AS driver_name
FROM drivers d
JOIN results re ON d.driverId = re.driverId
JOIN races r ON re.raceId = r.raceId
WHERE re.positionOrder <= 3 AND strftime('%Y', r.date) = '2011'

Challenging Difficulty

Question: Find the circuits where the average lap time in the first lap is slower than the overall average lap time across all circuits. List the circuit names
Evidence: This requires calculating averages across different groupings and comparing them
SQL: SELECT c.name AS circuit_name
FROM circuits c
JOIN races r ON c.circuitId = r.circuitId
JOIN lapTimes lt ON r.raceId = lt.raceId
WHERE lt.lap = 1
GROUP BY c.circuitId, c.name
HAVING AVG(lt.milliseconds) > (
SELECT AVG(milliseconds)
FROM lapTimes
)

Question:  Identify the drivers who have participated in races in at least 3 different countries. List their full names
Evidence:  This requires joining drivers, results, races, and circuits, then grouping and counting distinct countries
SQL: SELECT
d.forename || ' ' || d.surname AS driver_name
FROM drivers d
JOIN results re ON d.driverId = re.driverId
JOIN races r ON re.raceId = r.raceId
JOIN circuits ci ON r.circuitId = ci.circuitId
GROUP BY d.driverId, d.forename, d.surname
HAVING COUNT(DISTINCT ci.country) >= 3

Question:  For each year, find the constructor that achieved the most wins. Show the year, constructor name, and the number of wins
Evidence: Most wins requires finding MAX(wins) for each year in constructorStandingsSQL: SELECT
r.year,
co.name AS constructor_name,
cs.wins
FROM constructorStandings cs
JOIN races r ON cs.raceId = r.raceId
JOIN constructors co ON cs.constructorId = co.constructorId
WHERE cs.wins = (
SELECT MAX(wins)
FROM constructorStandings cs2
JOIN races r2 ON cs2.raceId = r2.raceId
WHERE r2.year = r.year
)

Question: Find the pairs of drivers who have the same birthday and have both participated in the same race at least once. Show their full names
Evidence: Same birthday and participated in the same race requires joining and filtering on these conditions
SQL: SELECT
d1.forename || ' ' || d1.surname AS driver1_name,
d2.forename || ' ' || d2.surname AS driver2_name
FROM drivers d1
JOIN drivers d2 ON d1.birthday = d2.birthday AND d1.driverId < d2.driverId
WHERE EXISTS (
SELECT 1
FROM results re1
JOIN results re2 ON re1.raceId = re2.raceId
WHERE re1.driverId = d1.driverId AND re2.driverId = d2.driverId
)

Question: Calculate the average potential rating for each position (positionOrder) in the 'Italian Serie A' league across all seasons.Evidence: 'Italian Serie A' is a name in the League table; average potential requires grouping and calculating AVG(potential)
SQL: SELECT
ds.positionOrder,
AVG(pa.potential) as avg_potential
FROM driverStandings ds
JOIN Player_Attributes pa ON ds.driverId = pa.player_api_id
JOIN Match m ON ds.raceId = m.id
JOIN League l ON m.league_id = l.id
WHERE l.name = 'Italian Serie A'
GROUP BY ds.positionOrder
"""

thrombosis_prediction_kgq = """
Simple Difficulty

Question: List the IDs of all patients diagnosed with 'MCTD'.Evidence: 'MCTD' is a value in the Diagnosis column of the Patient table
SQL: SELECT ID FROM Patient WHERE Diagnosis = 'MCTD'

Question: How many patients have an 'aCL IgM' value greater than 10?Evidence:  'aCL IgM' value greater than 10 refers to aCL IgM > 10 in the Examination table
SQL: SELECT COUNT(*) FROM Examination WHERE aCL IgM > 10

Question: Find the average 'RBC' (red blood cell count) for all patients
Evidence: Average 'RBC' refers to AVG(RBC) in the Laboratory table
SQL: SELECT AVG(RBC) FROM Laboratory

Question: List the distinct 'ANA Pattern' observed in the Examination table.Evidence: No specific evidence needed, it's about exploring the table
SQL: SELECT DISTINCT ANA Pattern FROM Examination

Question: How many patients have a 'Thrombosis' level of 2 (severe thrombosis) in their examination?Evidence: 'Thrombosis' level of 2 refers to Thrombosis = 2 in the Examination table
SQL: SELECT COUNT(*) FROM Examination WHERE Thrombosis = 2

Moderate Difficulty

Question:  What is the average 'TG' (triglyceride) level for 'male' patients?Evidence: 'male' refers to SEX = 'M' in the Patient table
SQL: SELECT AVG(l.TG)
FROM Laboratory l
JOIN Patient p ON l.ID = p.ID
WHERE p.SEX = 'M'

Question: List the IDs and birthdates of patients who have 'headache' as one of their symptoms and were born before 1960
Evidence: 'headache' is a value in the Symptoms column; born before 1960 refers to Birthday < '1960-01-01'
SQL: SELECT p.ID, p.Birthday
FROM Patient p
JOIN Examination e ON p.ID = e.ID
WHERE e.Symptoms LIKE '%headache%' AND p.Birthday < '1960-01-01'

Question:  Find the number of 'female' patients who have a 'CRP' (C-reactive protein) value of '2+' or higher
Evidence: 'female' refers to SEX = 'F'; 'CRP' value of '2+' or higher can be represented as CRP IN ('2+', '3+', '4+')
SQL: SELECT COUNT(*)
FROM Patient p
JOIN Laboratory l ON p.ID = l.ID
WHERE p.SEX = 'F' AND l.CRP IN ('2+', '3+', '4+')

Question: List the Diagnosis and the average Age for patients who have an UN (urea nitrogen) level above 29
Evidence: UN level above 29 refers to UN > 29; Age needs to be calculated based on BirthdaySQL: SELECT
p.Diagnosis,
AVG(strftime('%Y', 'now') - strftime('%Y', p.Birthday)) as avg_age
FROM Patient p
JOIN Laboratory l ON p.ID = l.ID
WHERE l.UN > 29
GROUP BY p.Diagnosis

Question:  Find the difference in the number of 'male' and 'female' patients who have been diagnosed with 'SLE'
Evidence: 'male' refers to SEX = 'M'; 'female' refers to SEX = 'F'; 'SLE' is a DiagnosisSQL: SELECT
SUM(CASE WHEN SEX = 'M' THEN 1 ELSE 0 END) -
SUM(CASE WHEN SEX = 'F' THEN 1 ELSE 0 END) AS gender_difference
FROM Patient
WHERE Diagnosis = 'SLE'

Challenging Difficulty

Question: Identify the patients who have had at least 2 Examinations with an aCL IgG value greater than the average aCL IgG value across all examinations. List their IDs and the number of such examinations
Evidence:  aCL IgG value greater than average requires calculating the overall average first; at least 2 examinations involves counting the number of examinations per patient
SQL: SELECT
p.ID,
COUNT() as num_exams_with_high_acl
FROM Patient p
JOIN Examination e ON p.ID = e.ID
WHERE e.aCL IgG > (SELECT AVG(aCL IgG) FROM Examination)
GROUP BY p.ID
HAVING COUNT() >= 2

Question:  Find the patients who have an abnormal T-CHO (total cholesterol) level but a normal TG (triglyceride) level. List their IDs and their DiagnosisEvidence: Abnormal T-CHO refers to T-CHO >= 250; normal TG refers to TG < 200
SQL: SELECT DISTINCT
p.ID,
p.Diagnosis
FROM Patient p
JOIN Laboratory l ON p.ID = l.ID
WHERE l.T-CHO >= 250 AND l.TG < 200

Question: Calculate the average Age for each Diagnosis, but only include diagnoses that have at least 5 'female' patients associated with them
Evidence:  Average Age requires calculating based on Birthday; at least 5 'female' patients implies filtering on SEX = 'F' and counting
SQL: SELECT
p.Diagnosis,
AVG(strftime('%Y', 'now') - strftime('%Y', p.Birthday)) as avg_age
FROM Patient p
WHERE p.SEX = 'F'
GROUP BY p.Diagnosis
HAVING COUNT(*) >= 5

Question: Find the patients who have a CRP (C-reactive protein) value higher than all patients diagnosed with 'RA'. List their IDs
Evidence: 'RA' is a Diagnosis; requires comparing CRP values across different groups
SQL: SELECT DISTINCT l.ID
FROM Laboratory l
WHERE l.CRP > ALL (
SELECT l2.CRP
FROM Laboratory l2
JOIN Patient p ON l2.ID = p.ID
WHERE p.Diagnosis = 'RA'
)

Question:  For each distinct Symptoms value, find the average HGB (hemoglobin) level across all associated Laboratory tests
Evidence:  Average HGB requires joining Examination and Laboratory and calculating the average; grouping by SymptomsSQL: SELECT
e.Symptoms,
AVG(l.HGB) as avg_hgb
FROM Examination e
JOIN Laboratory l ON e.ID = l.ID
GROUP BY e.Symptoms
"""


superhero_kgq = """
**Simple Difficulty:**

Question: List all superheroes with green hair.Evidence: green hair refers to colour = 'Green' and hair_colour_id = colour.id;
SQL: SELECT T1.superhero_name FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.hair_colour_id = T2.id WHERE T2.colour = 'Green'

Question: What is the skin color of the superhero named 'Thor'?Evidence: Thor refers to superhero_name = 'Thor'; color of skin refers to colour where skin_colour_id = colour.id
SQL: SELECT T2.colour FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.skin_colour_id = T2.id WHERE T1.superhero_name = 'Thor'

Question: How many superheroes are published by 'Image Comics'?Evidence: published by 'Image Comics' refers to publisher_name = 'Image Comics'
SQL: SELECT COUNT(T1.id) FROM superhero AS T1 INNER JOIN publisher AS T2 ON T1.publisher_id = T2.id WHERE T2.publisher_name = 'Image Comics'

Question: What is the gender of the superhero 'Wonder Woman'?Evidence: Wonder Woman refers to superhero_name = 'Wonder Woman'
SQL: SELECT T2.gender FROM superhero AS T1 INNER JOIN gender AS T2 ON T1.gender_id = T2.id WHERE T1.superhero_name = 'Wonder Woman'

Question: List the superpowers of the superhero with ID 10.Evidence: superpowers refers to power_name
SQL: SELECT T2.power_name FROM hero_power AS T1 INNER JOIN superpower AS T2 ON T1.power_id = T2.id WHERE T1.hero_id = 10

**Moderate Difficulty:**

Question: Among superheroes taller than 190cm, how many have the power of 'Flight'?Evidence: taller than 190cm refers to height_cm > 190; power of 'Flight' refers to power_name = 'Flight'
SQL: SELECT COUNT(T1.id) FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id INNER JOIN superpower AS T3 ON T2.power_id = T3.id WHERE T1.height_cm > 190 AND T3.power_name = 'Flight'

Question: List the full names of all superheroes with green eyes and red hair.Evidence: green eyes refers to colour = 'Green' and eye_colour_id = colour.id; red hair refers to colour = 'Red' and hair_colour_id = colour.id
SQL: SELECT T1.full_name FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.eye_colour_id = T2.id INNER JOIN colour AS T3 ON T1.hair_colour_id = T3.id WHERE T2.colour = 'Green' AND T3.colour = 'Red'

Question: Rank the publishers by the average strength of their superheroes, in descending order.Evidence: average strength refers to AVG(attribute_value) WHERE attribute_name = 'Strength'
SQL: SELECT T2.publisher_name, AVG(T3.attribute_value) as avg_strength FROM superhero AS T1 INNER JOIN publisher AS T2 ON T1.publisher_id = T2.id INNER JOIN hero_attribute AS T3 ON T1.id = T3.hero_id INNER JOIN attribute AS T4 ON T3.attribute_id = T4.id WHERE T4.attribute_name = 'Strength' GROUP BY T2.publisher_name ORDER BY avg_strength DESC

Question: What is the average weight of superheroes with the power of 'Telepathy'?Evidence: power of 'Telepathy' refers to power_name = 'Telepathy'; average weight refers to AVG(weight_kg)
SQL: SELECT AVG(T1.weight_kg) FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id INNER JOIN superpower AS T3 ON T2.power_id = T3.id WHERE T3.power_name = 'Telepathy'

Question: List the superheroes from DC Comics who have an intelligence attribute value greater than 90.Evidence: DC Comics refers to publisher_name = 'DC Comics'; intelligence attribute value greater than 90 refers to attribute_name = 'Intelligence' AND attribute_value > 90
SQL: SELECT T1.superhero_name FROM superhero AS T1 INNER JOIN hero_attribute AS T2 ON T1.id = T2.hero_id INNER JOIN attribute AS T3 ON T2.attribute_id = T3.id INNER JOIN publisher AS T4 ON T1.publisher_id = T4.id WHERE T3.attribute_name = 'Intelligence' AND T2.attribute_value > 90 AND T4.publisher_name = 'DC Comics'

**Challenging Difficulty:**

Question: Among superheroes with black hair, what is the percentage of those who are also villains?Evidence: black hair refers to colour = 'Black' and hair_colour_id = colour.id; villains refers to alignment = 'Bad'; calculation = MULTIPLY(DIVIDE(SUM(alignment = 'Bad'), COUNT(*)), 100)
SQL: SELECT CAST(COUNT(CASE WHEN T3.alignment = 'Bad' THEN 1 ELSE NULL END) AS REAL) * 100 / COUNT(T1.id) FROM superhero AS T1 INNER JOIN colour AS T2 ON T1.hair_colour_id = T2.id INNER JOIN alignment AS T3 ON T1.alignment_id = T3.id WHERE T2.colour = 'Black'

Question: List the superhero names and their publishers for those who have both 'Super Strength' and 'Flight' as their superpowers.Evidence: 'Super Strength' refers to power_name = 'Super Strength'; 'Flight' refers to power_name = 'Flight'; publisher refers to publisher_name
SQL: SELECT T1.superhero_name, T5.publisher_name FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id INNER JOIN superpower AS T3 ON T2.power_id = T3.id INNER JOIN publisher AS T5 ON T1.publisher_id = T5.id WHERE T3.power_name IN ('Super Strength', 'Flight') GROUP BY T1.superhero_name, T5.publisher_name HAVING COUNT(DISTINCT T3.power_name) = 2

Question: Find the average speed of superheroes published by Marvel Comics who also have the power of 'Invulnerability'.Evidence: Marvel Comics refers to publisher_name = 'Marvel Comics'; power of 'Invulnerability' refers to power_name = 'Invulnerability'; average speed refers to AVG(attribute_value) WHERE attribute_name = 'Speed'
SQL: SELECT AVG(T3.attribute_value) FROM superhero AS T1 INNER JOIN hero_power AS T2 ON T1.id = T2.hero_id INNER JOIN superpower AS T4 ON T2.power_id = T4.id INNER JOIN hero_attribute AS T3 ON T1.id = T3.hero_id INNER JOIN attribute AS T5 ON T3.attribute_id = T5.id INNER JOIN publisher AS T6 ON T1.publisher_id = T6.id WHERE T4.power_name = 'Invulnerability' AND T5.attribute_name = 'Speed' AND T6.publisher_name = 'Marvel Comics'

Question: Which publisher has the highest ratio of male to female superheroes?Evidence: male refers to gender = 'Male'; female refers to gender = 'Female'; ratio = DIVIDE(SUM(gender = 'Male'), SUM(gender = 'Female'))
SQL: SELECT T2.publisher_name, CAST(SUM(CASE WHEN T3.gender = 'Male' THEN 1 ELSE 0 END) AS REAL) / SUM(CASE WHEN T3.gender = 'Female' THEN 1 ELSE 0 END) as gender_ratio FROM superhero AS T1 INNER JOIN publisher AS T2 ON T1.publisher_id = T2.id INNER JOIN gender AS T3 ON T1.gender_id = T3.id GROUP BY T2.publisher_name ORDER BY gender_ratio DESC LIMIT 1

Question: Find the top 3 superpowers that are most common among superheroes with blue eyes.Evidence: blue eyes refers to colour = 'Blue' and eye_colour_id = colour.id; most common refers to COUNT() DESC
SQL: SELECT T3.power_name, COUNT() as power_count

"""



student_club_kgq = """
Simple Difficulty:

Question: What is the phone number of the student named 'John Smith'?Evidence: John Smith is the full name; full name refers to first_name, last_name;
SQL: SELECT phone FROM member WHERE first_name = 'John' AND last_name = 'Smith'

Question: How many students are majoring in 'Computer Science'?Evidence: 'Computer Science' is the major_name
SQL: SELECT COUNT(T1.member_id) FROM member AS T1 INNER JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T2.major_name = 'Computer Science'

Question: List the event names of all events that took place in 'Room 101'.Evidence: 'Room 101' is the location
SQL: SELECT event_name FROM event WHERE location = 'Room 101'

Question: What is the t-shirt size of the student with member ID 'rec12345'?Evidence: 'rec12345' is the member_id
SQL: SELECT t_shirt_size FROM member WHERE member_id = 'rec12345'

Question: List the zip codes of all students who attended the 'Spring Fling' event.Evidence: 'Spring Fling' is an event name
SQL: SELECT T3.zip FROM event AS T1 INNER JOIN attendance AS T2 ON T1.event_id = T2.link_to_event INNER JOIN member AS T3 ON T2.link_to_member = T3.member_id WHERE T1.event_name = 'Spring Fling'

Moderate Difficulty:

Question: Among students from the 'College of Science', how many attended the 'Movie Night' event?Evidence: 'College of Science' is the college; 'Movie Night' is an event name
SQL: SELECT COUNT(T3.member_id) FROM major AS T1 INNER JOIN member AS T2 ON T1.major_id = T2.link_to_major INNER JOIN attendance AS T3 ON T2.member_id = T3.link_to_member INNER JOIN event AS T4 ON T3.link_to_event = T4.event_id WHERE T1.college = 'College of Science' AND T4.event_name = 'Movie Night'

Question: List the email addresses of all students who want a 'Large' t-shirt and are majoring in 'Biology'.Evidence: 'Large' is a t_shirt_size; 'Biology' is a major_name
SQL: SELECT T1.email FROM member AS T1 INNER JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T1.t_shirt_size = 'Large' AND T2.major_name = 'Biology'

Question: What is the total amount of funds received from 'Donations' in the year 2020?Evidence: 'Donations' is a source; funds received refers to amount; in the year 2020 refers to YEAR(date_received) = 2020
SQL: SELECT SUM(amount) FROM income WHERE source = 'Donations' AND SUBSTR(date_received, 1, 4) = '2020'

Question: List the event names and dates for all events that had a budget for 'Food' exceeding $50.Evidence: budget for 'Food' refers to category = 'Food'; exceeding $50 refers to amount > 50
SQL: SELECT T2.event_name, T2.event_date FROM budget AS T1 INNER JOIN event AS T2 ON T1.link_to_event = T2.event_id WHERE T1.category = 'Food' AND T1.amount > 50

Question: What is the average cost of expenses for events that took place in 'Auditorium A'?Evidence: 'Auditorium A' is a location; average cost of expenses refers to AVG(cost)
SQL: SELECT AVG(T2.cost) FROM event AS T1 INNER JOIN budget AS T3 ON T1.event_id = T3.link_to_event INNER JOIN expense AS T2 ON T3.budget_id = T2.link_to_budget WHERE T1.location = 'Auditorium A'

Challenging Difficulty:

Question: Find the top 3 majors with the highest average attendance at 'Social' events.Evidence: 'Social' is an event type; average attendance refers to AVG(COUNT(*))
SQL: SELECT T2.major_name, AVG(attendance_count) as avg_attendance
FROM major AS T2
INNER JOIN member AS T3 ON T2.major_id = T3.link_to_major
INNER JOIN attendance AS T4 ON T3.member_id = T4.link_to_member
INNER JOIN event AS T5 ON T4.link_to_event = T5.event_id
WHERE T5.type = 'Social'
GROUP BY T2.major_name
ORDER BY avg_attendance DESC
LIMIT 3

Question: List the full names of members who attended all events that took place in the 'Conference Room'.Evidence: full name refers to first_name, last_name; 'Conference Room' is a location
SQL: SELECT T3.first_name, T3.last_name
FROM event AS T1
INNER JOIN attendance AS T2 ON T1.event_id = T2.link_to_event
INNER JOIN member AS T3 ON T2.link_to_member = T3.member_id
WHERE T1.location = 'Conference Room'
GROUP BY T3.member_id
HAVING COUNT(DISTINCT T1.event_id) = (
SELECT COUNT(*)
FROM event
WHERE location = 'Conference Room'
)

Question: For each college, calculate the ratio of the total income generated to the total expenses incurred by its students.Evidence: total income generated refers to SUM(income.amount); total expenses incurred refers to SUM(expense.cost)
SQL: SELECT
M.college,
CAST(SUM(I.amount) AS REAL) / SUM(E.cost) AS ratio
FROM major M
JOIN member MB ON M.major_id = MB.link_to_major
LEFT JOIN income I ON MB.member_id = I.link_to_member
LEFT JOIN expense E ON MB.member_id = E.link_to_member
GROUP BY M.college

Question: Find the events where the actual spending on 'Food' exceeded the budgeted amount for 'Food' by more than 20%.Evidence: actual spending on 'Food' refers to spent WHERE category = 'Food'; budgeted amount for 'Food' refers to amount WHERE category = 'Food'; exceeded by more than 20% refers to (spent - amount) / amount > 0.2
SQL: SELECT
E.event_name
FROM event E
JOIN budget B ON E.event_id = B.link_to_event
WHERE B.category = 'Food'
AND (B.spent - B.amount) / B.amount > 0.2

Question: Identify the member who has attended the most events and also generated the highest income for the club.Evidence: attended the most events refers to MAX(COUNT(attendance.link_to_event)); generated the highest income refers to MAX(income.amount)
SQL: WITH
Most_attended AS (
SELECT link_to_member, COUNT() as event_count
FROM attendance
GROUP BY link_to_member
ORDER BY event_count DESC
LIMIT 1
),
Highest_income AS (
SELECT link_to_member, SUM(amount) as total_income
FROM income
GROUP BY link_to_member
ORDER BY total_income DESC
LIMIT 1
)
SELECT M.
FROM member M
WHERE M.member_id IN (
SELECT link_to_member FROM Most_attended
INTERSECT
SELECT link_to_member FROM Highest_income
)
"""



def retrieve_kgq_examples(dataset): 
    if dataset == 'california_schools':
        return california_schools_kgq

    elif dataset == 'card_games':
        return card_games_kgq
    
    elif dataset == 'codebase_community':
        return codebase_community_kgq
    
    elif dataset == 'debit_card_specializing':
        return debit_card_specializing_kgq
    
    elif dataset == 'financial':
        return financial_kgq
    
    elif dataset == 'superhero':
        return superhero_kgq
    
    elif dataset == 'toxicology':
        return toxicology_kgq
    
    elif dataset == 'european_football_2':
        return european_football_2_kgq

    elif dataset == 'formula_1':
        return formula_1_kgq
    
    elif dataset == 'thrombosis_prediction': 
        return thrombosis_prediction_kgq
    
    elif dataset == 'student_club': 
        return student_club_kgq