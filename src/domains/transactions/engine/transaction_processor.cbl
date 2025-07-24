IDENTIFICATION DIVISION.
       PROGRAM-ID. TRANSACTION-PROCESSOR.
       AUTHOR. Gemini.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT TRANSACTION-IN ASSIGN TO KEYBOARD
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS FS-TRANSACTION-IN.
           SELECT REPORT-OUT ASSIGN TO DISPLAY
               ORGANIZATION IS LINE SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS FS-REPORT-OUT.

       DATA DIVISION.
       FILE SECTION.
       FD  TRANSACTION-IN
           RECORD CONTAINS 59 CHARACTERS
           DATA RECORD IS TRANSACTION-RECORD.
       01  TRANSACTION-RECORD.
           COPY "transaction_record.cpy".

       FD  REPORT-OUT.
       01  REPORT-RECORD.
           05 RP-TOTAL-TRANSACTIONS   PIC 9(08).
           05 FILLER                  PIC X(01) VALUE ','.
           05 RP-TOTAL-AMOUNT         PIC -9(13).99.

       WORKING-STORAGE SECTION.
       01  WS-WORK-AREAS.
           05 WS-EOF                  PIC A(1) VALUE 'N'.
           05 WS-COUNTER              PIC 9(8) VALUE 0.
           05 WS-TOTAL-AMOUNT         PIC S9(13)V99 VALUE 0.
           05 WS-EXIT-CODE            PIC 9(1) VALUE 0.

       01  FILE-STATUS-CODES.
           05 FS-TRANSACTION-IN       PIC X(2).
           05 FS-REPORT-OUT           PIC X(2).

       PROCEDURE DIVISION.
       MAIN-PROCEDURE.

           OPEN INPUT TRANSACTION-IN
           IF FS-TRANSACTION-IN NOT = "00"
              DISPLAY "Fatal: Error opening input file. Status: " FS-TRANSACTION-IN UPON SYSERR
              MOVE 1 TO WS-EXIT-CODE
              GO TO CLEANUP-AND-EXIT
           END-IF

           OPEN OUTPUT REPORT-OUT
           IF FS-REPORT-OUT NOT = "00"
              DISPLAY "Fatal: Error opening output file. Status: " FS-REPORT-OUT UPON SYSERR
              MOVE 1 TO WS-EXIT-CODE
              GO TO CLEANUP-AND-EXIT
           END-IF

           PERFORM PROCESS-RECORDS UNTIL WS-EOF = 'Y'

           MOVE WS-COUNTER TO RP-TOTAL-TRANSACTIONS
           MOVE WS-TOTAL-AMOUNT TO RP-TOTAL-AMOUNT
           WRITE REPORT-RECORD
           IF FS-REPORT-OUT NOT = "00"
               DISPLAY "Fatal: Error writing to output file. Status: " FS-REPORT-OUT UPON SYSERR
               MOVE 1 TO WS-EXIT-CODE
           END-IF.

       CLEANUP-AND-EXIT.
           CLOSE TRANSACTION-IN
           CLOSE REPORT-OUT
           STOP RUN WS-EXIT-CODE.

       PROCESS-RECORDS.
           READ TRANSACTION-IN
               AT END
                   SET WS-EOF TO 'Y'
               NOT AT END
                   IF FS-TRANSACTION-IN = "00"
                       ADD 1 TO WS-COUNTER
                       ADD TR-AMOUNT TO WS-TOTAL-AMOUNT
                   ELSE
                       DISPLAY "Warning: Error reading input record. Status: " FS-TRANSACTION-IN UPON SYSERR
                       SET WS-EOF TO 'Y'
                       MOVE 1 TO WS-EXIT-CODE
                   END-IF
           END-READ.

       END PROGRAM TRANSACTION-PROCESSOR.
