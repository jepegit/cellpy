# Issue #989: Check capacity calculation behavior

Source: https://github.com/jepegit/cellpy/issues/989

## Original issue text

I have some data which directly imported into cellpy 1.x produced this plot (the problem existed both for charge and discharge):

<img width="1905" height="501" alt="Image" src="https://github.com/user-attachments/assets/01b53418-3f4c-408c-960a-2a49014d07c3" />

In cellpy 2.1.3.post 2, I get this:

<img width="897" height="328" alt="Image" src="https://github.com/user-attachments/assets/aba3b5c5-63ea-4345-9669-ef096492f787" />

The initial double capacity was caused by forgetting to reset the capacity in a given step where it should have been reset. Somehow cellpy 2.x handles this automatically. Is this documented? Additionally, a message indicating that this correction was performed would be nice to have.
