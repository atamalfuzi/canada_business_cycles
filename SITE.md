# Proposed site text

For the session that integrates the website. Nothing here has been added to the site.

## Portfolio entry

**Title:** How three filters read Canada's business cycles, and what they make of 2020

**Type and year:** Open data analysis in Python, 2026

**Text:** How Canadian output, consumption, investment, government purchases and net exports rise and fall around their long-run growth, from 1961 to 2026, on Statistics Canada data. Investment accounts for most of the swings in output, and net exports lean weakly against them. The 2020 fall looks different under each of three common filters, and one of them shows a boom two years later that comes from the method.

**Links:** Project page, and code at https://github.com/atamalfuzi/canada_business_cycles

## Project page

### Summary

Canada's economy has grown by about 3% a year on average since 1961, but not steadily. The business cycle is the rise and fall around that growth. To measure it you first decide what normal output is at each date, called the trend, and then measure how far actual output is above or below it. I compare three common ways of doing this on Canadian national accounts: the Hodrick-Prescott filter, the Baxter-King filter and the Hamilton projection.

Data run from 1961 to 2026 (through 2026Q2), from Statistics Canada table 36-10-0104. Recession dates come from the C.D. Howe Institute Business Cycle Council.

### How the three filters work

Figure: `figures/trends.png`

Hodrick-Prescott draws a smooth curve through the data, and its reading of recent years can change as new data arrive. Baxter-King keeps only movements that repeat every one and a half to eight years, and has no value for the first and last three years. Hamilton compares output with what you would have predicted two years earlier from its own past values, so it uses only the past.

### How the parts of output move

Figure: `figures/hodrick_prescott.png`. The other two filters are `figures/baxter_king.png` and `figures/hamilton.png`, on the same vertical scale, and could sit behind a link or a toggle.

Investment swings 3.4 to 3.7 times as far as output and moves closely with it. Consumption also moves with output, and government purchases are close to unrelated to it. Through 2019, consumption is the least volatile series under all three filters. In 2020 it fell further than output, which it had not done in earlier recessions under two of the three filters.

### Net exports

Figure: `figures/net_exports.png`

Net exports are sometimes negative, so they have no log. Dividing each series by the trend of output gets around this, and it also shows how much each part contributes. On this measure investment accounts for 71% of the variance in output, and consumption for 36%.

Net exports lean against output, weakly. The correlation with output is −0.21, with a 95% range of −0.44 to 0.06, and it is about zero since 1990. They rose during the 1981-82, 2008-09 and 2020 recessions and barely moved in the other two.

### 2020 against earlier recessions

Figures: `figures/pandemic.png`, then `figures/output_gaps.png`

Log output fell 13.6 points from 2019Q4 to 2020Q2, about four times the average of the four earlier recessions. Baxter-King shows −5.8, about twice its usual low, because it drops much of a fall and recovery that fast. Hodrick-Prescott shows −12.3, and its trend bends down to meet the fall, lifting 2019 by up to 1.7 points. Hamilton shows −13.9, then +11.5 in 2022Q2, when its prediction is based on the low quarters of 2020. That is its largest reading in the sample. If the pandemic is replaced with a straight line, 10.6 points of it go away.

### Which filter to use

For describing past cycles, I would use Hodrick-Prescott. Its low falls in the dated trough quarter in all five recessions, output is above trend at all five peaks, and 2020 moves other quarters less than it does under the other filters. For judging the most recent quarter I would use Hamilton. Hodrick-Prescott's first reading has the wrong sign 37% of the time once later data arrive, against 12% for Hamilton, and Baxter-King has no reading for the last three years.

These tests lean toward filters that follow output closely, and the recession dates rest partly on GDP. They also don't test Hamilton's argument that Hodrick-Prescott can create cycles where there are none.

### Notes for the page

- Use the "Personal project" disclaimer from the README.
- Keep the note that results describe Statistics Canada's file dated August 28, 2026.
- The tables in the README can be reused as they are. The source numbers are in `output/`.
