* COPYBOOK for TRANSACTION-RECORD (Binary Format)
      * Total Record Length: 5 + 8 + 20 + 26 = 59 bytes
      01 TRANSACTION-RECORD-BINARY.
         05 TR-ID                  PIC S9(9)  COMP-3.
         05 TR-AMOUNT              PIC S9(13)V99 COMP-3.
         05 TR-CATEGORY            PIC X(20).
         05 TR-TIMESTAMP           PIC X(26).