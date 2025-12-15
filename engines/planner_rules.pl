% ---------- Utility ----------
days_between(date(Y1,M1,D1), date(Y2,M2,D2), K) :-
    date_time_stamp(date(Y1,M1,D1,0,0,0,0,-,-), S1),
    date_time_stamp(date(Y2,M2,D2,0,0,0,0,-,-), S2),
    K is round((S2 - S1) / 86400).

today(T) :- get_time(Now), stamp_date_time(Now, date(Y,M,D,_,_,_,_,_,_), 'UTC'),
            T = date(Y,M,D).

% Facts to be asserted at runtime:
% hours_per_day(Minutes).
% subject(math). difficulty(math,3).
% deadline(math, exam, date(2025,10,28)).
% progress(math, completion_pct, 0.65).

near_exam(S) :-
  deadline(S, exam, Dt),
  exam_near_days(Near),
  today(T),
  days_between(T, Dt, K),
  K >= 0,
  K =< Near.


allocate(S, Minutes) :-
  hours_per_day(H),
  ( near_exam(S) -> Minutes0 is min(120, 0.5 * H)
  ; ( progress(S, completion_pct, P), P < 0.7 -> Minutes0 is min(90, 0.4 * H)
    ; ( difficulty(S, D), D >= 4 -> Minutes0 is min(75, 0.35 * H)
      ; Minutes0 is min(60, 0.25 * H) ))),
  Minutes is round(Minutes0).

decision(S, needs_info) :- \+ deadline(S,_,_), !.
decision(S, reject)     :- allocate(S, M), M < 30, !.
decision(S, shortlist)  :- allocate(S, M), M >= 30.

plan_triplet(S, Decision, Minutes) :-
  subject(S), (decision(S, Decision) -> true ; Decision = needs_info),
  (allocate(S, Minutes) -> true ; Minutes = 0).

% entry point: prints JSON-like terms for Python to parse
main :-
  findall([S,D,M], plan_triplet(S,D,M), L),
  write(L), nl.
