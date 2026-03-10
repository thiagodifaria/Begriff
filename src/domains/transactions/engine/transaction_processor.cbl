       IDENTIFICATION DIVISION.
       PROGRAM-ID. TRANSACTION-PROCESSOR.

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
           RECORD CONTAINS 59 CHARACTERS.
       01  TRANSACTION-RECORD.
           COPY "transaction_record.cpy".

       FD  REPORT-OUT.
       01  REPORT-RECORD.
           05 RP-TOTAL-TRANSACTIONS   PIC 9(08).
           05 FILLER                  PIC X(01) VALUE SPACE.
           05 RP-TOTAL-AMOUNT         PIC S9(13)V99.

       WORKING-STORAGE SECTION.
       01  WS-WORK-AREAS.
           05 WS-EOF                  PIC X(1) VALUE 'N'.
           05 WS-COUNTER              PIC 9(8) VALUE 0.
           05 WS-TOTAL-AMOUNT         PIC S9(13)V99 VALUE 0.
           05 WS-INVALID-COUNT        PIC 9(8) VALUE 0.
           05 WS-EXIT-CODE            PIC 9(1) VALUE 0.

       01  FILE-STATUS-CODES.
           05 FS-TRANSACTION-IN       PIC X(2).
           05 FS-REPORT-OUT           PIC X(2).

       01  WS-VALIDATION.
           05 WS-RECORD-VALID         PIC X(1) VALUE 'Y'.
           05 WS-YEAR-TEXT            PIC X(4).
           05 WS-MONTH-TEXT           PIC X(2).
           05 WS-DAY-TEXT             PIC X(2).
           05 WS-YEAR-NUM             PIC 9(4).
           05 WS-MONTH-NUM            PIC 99.
           05 WS-DAY-NUM              PIC 99.
           05 WS-MAX-AMOUNT           PIC S9(13)V99 VALUE 9999999999999.99.
           05 WS-MIN-AMOUNT           PIC S9(13)V99 VALUE -9999999999999.99.

       PROCEDURE DIVISION.
       MAIN-PROCEDURE.
           OPEN INPUT TRANSACTION-IN
           IF FS-TRANSACTION-IN NOT = "00"
              MOVE 1 TO WS-EXIT-CODE
              GO TO CLEANUP-AND-EXIT
           END-IF

           OPEN OUTPUT REPORT-OUT
           IF FS-REPORT-OUT NOT = "00"
              MOVE 1 TO WS-EXIT-CODE
              GO TO CLEANUP-AND-EXIT
           END-IF

           PERFORM UNTIL WS-EOF = 'Y'
               READ TRANSACTION-IN
                   AT END
                       MOVE 'Y' TO WS-EOF
                   NOT AT END
                       IF FS-TRANSACTION-IN = "00"
                           PERFORM VALIDATE-RECORD
                           IF WS-RECORD-VALID = 'Y'
                               ADD 1 TO WS-COUNTER
                               ADD TR-AMOUNT TO WS-TOTAL-AMOUNT
                           ELSE
                               ADD 1 TO WS-INVALID-COUNT
                           END-IF
                       ELSE
                           MOVE 'Y' TO WS-EOF
                           MOVE 1 TO WS-EXIT-CODE
                       END-IF
               END-READ
           END-PERFORM

           MOVE WS-COUNTER TO RP-TOTAL-TRANSACTIONS
           MOVE WS-TOTAL-AMOUNT TO RP-TOTAL-AMOUNT
           WRITE REPORT-RECORD
           IF FS-REPORT-OUT NOT = "00"
               MOVE 1 TO WS-EXIT-CODE
           END-IF

       CLEANUP-AND-EXIT.
           CLOSE TRANSACTION-IN
           CLOSE REPORT-OUT
           STOP RUN WS-EXIT-CODE.

       VALIDATE-RECORD.
           MOVE 'Y' TO WS-RECORD-VALID

           IF TR-CATEGORY = SPACES
               MOVE 'N' TO WS-RECORD-VALID
           END-IF

           IF TR-AMOUNT > WS-MAX-AMOUNT OR TR-AMOUNT < WS-MIN-AMOUNT
               MOVE 'N' TO WS-RECORD-VALID
           END-IF

           MOVE TR-TIMESTAMP(1:4) TO WS-YEAR-TEXT
           MOVE TR-TIMESTAMP(6:2) TO WS-MONTH-TEXT
           MOVE TR-TIMESTAMP(9:2) TO WS-DAY-TEXT

           IF TR-TIMESTAMP(5:1) NOT = "-" OR TR-TIMESTAMP(8:1) NOT = "-"
               MOVE 'N' TO WS-RECORD-VALID
           END-IF

           IF WS-YEAR-TEXT IS NUMERIC
              MOVE FUNCTION NUMVAL(WS-YEAR-TEXT) TO WS-YEAR-NUM
           ELSE
              MOVE 'N' TO WS-RECORD-VALID
           END-IF

           IF WS-MONTH-TEXT IS NUMERIC
              MOVE FUNCTION NUMVAL(WS-MONTH-TEXT) TO WS-MONTH-NUM
           ELSE
              MOVE 'N' TO WS-RECORD-VALID
           END-IF

           IF WS-DAY-TEXT IS NUMERIC
              MOVE FUNCTION NUMVAL(WS-DAY-TEXT) TO WS-DAY-NUM
           ELSE
              MOVE 'N' TO WS-RECORD-VALID
           END-IF

           IF WS-MONTH-NUM < 1 OR WS-MONTH-NUM > 12
               MOVE 'N' TO WS-RECORD-VALID
           END-IF

           IF WS-DAY-NUM < 1 OR WS-DAY-NUM > 31
               MOVE 'N' TO WS-RECORD-VALID
           END-IF.

       END PROGRAM TRANSACTION-PROCESSOR.
