******************************************************************
      * COPYBOOK FOR THE RECONCILIATION SUMMARY REPORT
      * Defines the fixed-format layout for the output summary file.
      ******************************************************************
           05 RS-TOTAL-RECORDS      PIC 9(9).
           05 RS-TOTAL-DEBITS       PIC 9(15)V99.
           05 RS-TOTAL-CREDITS      PIC 9(15)V99.
           05 RS-HIGH-VALUE-FLAG    PIC X(1).
           05 RS-DUPLICATE-TX-FLAG  PIC X(1).
           05 RS-DATA-ERROR-FLAG    PIC X(1).