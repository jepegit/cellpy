# Issue #983: label issues when using direction=both when plotting ica

Source: https://github.com/jepegit/cellpy/issues/983

## Original issue text

```
cycles_collected = ica_collector(
    b,
    cycles=[1,3, 53, 103, 153, 203, 253, 303],
    voltage_resolution=0.005,
)

cycles_collected.plot(layout="per_cycle", direction='charge', height=800, width=1200)
```
produces this:
<img width="1200" height="800" alt="Image" src="https://github.com/user-attachments/assets/a4ae242a-757a-4862-8ca0-569faa0823e9" />

while using `direction='both'` produces this:

<img width="1200" height="800" alt="Image" src="https://github.com/user-attachments/assets/3858c360-683e-4e47-9907-de7bf0ab6a60" />

showing group number rather than cell label on the legend title. I think cell label is better/would be correct.
