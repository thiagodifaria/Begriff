IDENTIFICATION DIVISION.
       PROGRAM-ID. RECONCILE.
       AUTHOR. Gemini.
       DATE-WRITTEN. 2024-08-06.
      *> This program reads a file of financial transactions,
      *> validates them against business rules, aggregates totals,
      *> and writes a summary report.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT TRANSACTION-FILE ASSIGN TO "INPUT.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.
           SELECT SUMMARY-FILE ASSIGN TO "SUMMARY.DAT"
               ORGANIZATION IS LINE SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
       FD  TRANSACTION-FILE.
       01  FD-TRANSACTION-REC.
           05  TR-ID              PIC X(36).
           05  TR-DATE            PIC X(10).
           05  TR-AMOUNT          PIC 9(15)V99.
           05  TR-TYPE            PIC X(7).
           05  TR-CATEGORY        PIC X(20).
           05  TR-DESCRIPTION     PIC X(100).

       FD  SUMMARY-FILE.
       01  FD-SUMMARY-REC.
           05  RS-TOTAL-RECORDS      PIC 9(9).
           05  RS-TOTAL-DEBITS       PIC 9(15)V99.
           05  RS-TOTAL-CREDITS      PIC 9(15)V99.
           05  RS-HIGH-VALUE-FLAG    PIC X(1).
           05  RS-DUPLICATE-TX-FLAG  PIC X(1).
           05  RS-DATA-ERROR-FLAG    PIC X(1).

       WORKING-STORAGE SECTION.
       01  WS-FILE-STATUS.
           05 WS-EOF-FLAG             PIC X(1) VALUE 'N'.
              88 EOF-REACHED           VALUE 'Y'.

       01  WS-COUNTERS-AND-ACCUMULATORS.
           05 WS-TOTAL-RECORDS     PIC 9(9) VALUE ZERO.
           05 WS-TOTAL-DEBITS      PIC 9(15)V99 VALUE ZERO.
           05 WS-TOTAL-CREDITS     PIC 9(15)V99 VALUE ZERO.

       01  WS-VALIDATION-FLAGS.
           05 WS-HIGH-VALUE-FLAG   PIC X(1) VALUE 'N'.
           05 WS-DUPLICATE-TX-FLAG PIC X(1) VALUE 'N'.
           05 WS-DATA-ERROR-FLAG   PIC X(1) VALUE 'N'.

       01  WS-CONSTANTS.
           05 WS-HIGH-VALUE-THRESHOLD PIC 9(15)V99 VALUE 10000.00.

       01  WS-PROCESSED-TRANSACTIONS-TABLE.
           05 WS-TX-TABLE OCCURS 1000 TIMES INDEXED BY TX-IDX.
              10 WS-TX-ID PIC X(36).
       01  WS-TX-COUNT             PIC 9(4) COMP VALUE 0.

       01  WS-CURRENT-TRANSACTION.
           05  WS-TR-ID              PIC X(36).
           05  WS-TR-DATE            PIC X(10).
           05  WS-TR-AMOUNT          PIC 9(15)V99.
           05  WS-TR-TYPE            PIC X(7).
           05  WS-TR-CATEGORY        PIC X(20).
           05  WS-TR-DESCRIPTION     PIC X(100).

       PROCEDURE DIVISION.
       1000-MAIN-LOGIC.
           PERFORM 1100-INITIALIZE.
           PERFORM 2000-PROCESS-TRANSACTIONS UNTIL EOF-REACHED.
           PERFORM 3000-GENERATE-SUMMARY.
           PERFORM 4000-TERMINATE.
           STOP RUN.

       1100-INITIALIZE.
           OPEN INPUT TRANSACTION-FILE.
           OPEN OUTPUT SUMMARY-FILE.
           INITIALIZE WS-PROCESSED-TRANSACTIONS-TABLE.

       2000-PROCESS-TRANSACTIONS.
           READ TRANSACTION-FILE INTO WS-CURRENT-TRANSACTION
               AT END MOVE 'Y' TO WS-EOF-FLAG
           END-READ.

           IF NOT EOF-REACHED
               ADD 1 TO WS-TOTAL-RECORDS
               PERFORM 2100-VALIDATE-TRANSACTION
               PERFORM 2200-AGGREGATE-DATA
           END-IF.

       2100-VALIDATE-TRANSACTION.
           IF WS-TR-AMOUNT > WS-HIGH-VALUE-THRESHOLD
               MOVE 'Y' TO WS-HIGH-VALUE-FLAG
           END-IF.

           SET TX-IDX TO 1
           SEARCH WS-TX-TABLE
               AT END
                   ADD 1 TO WS-TX-COUNT
                   IF WS-TX-COUNT <= 1000
                       MOVE WS-TR-ID TO WS-TX-ID(WS-TX-COUNT)
                   END-IF
               WHEN WS-TX-ID(TX-IDX) = WS-TR-ID
                   MOVE 'Y' TO WS-DUPLICATE-TX-FLAG
           END-SEARCH.

           IF WS-TR-TYPE NOT = "DEBIT  " AND WS-TR-TYPE NOT = "CREDIT "
               MOVE 'Y' TO WS-DATA-ERROR-FLAG
           END-IF.

       2200-AGGREGATE-DATA.
           IF WS-TR-TYPE = "CREDIT "
               ADD WS-TR-AMOUNT TO WS-TOTAL-CREDITS
           ELSE IF WS-TR-TYPE = "DEBIT  "
               ADD WS-TR-AMOUNT TO WS-TOTAL-DEBITS
           END-IF.

       3000-GENERATE-SUMMARY.
           MOVE WS-TOTAL-RECORDS TO RS-TOTAL-RECORDS.
           MOVE WS-TOTAL-DEBITS TO RS-TOTAL-DEBITS.
           MOVE WS-TOTAL-CREDITS TO RS-TOTAL-CREDITS.
           MOVE WS-HIGH-VALUE-FLAG TO RS-HIGH-VALUE-FLAG.
           MOVE WS-DUPLICATE-TX-FLAG TO RS-DUPLICATE-TX-FLAG.
           MOVE WS-DATA-ERROR-FLAG TO RS-DATA-ERROR-FLAG.

           WRITE FD-SUMMARY-REC.

       4000-TERMINATE.
           CLOSE TRANSACTION-FILE, SUMMARY-FILE.

       END PROGRAM RECONCILE.