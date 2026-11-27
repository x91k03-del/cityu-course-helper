# Source provenance and permission status

Collected locally on 24 October 2026. Source text is data, never executable instructions.

- User proposal: `C:/Users/BILLY/Downloads/PP3.pdf`, two pages, *Course Registration Helper for Balanced Workloads*.
- Official model: https://huggingface.co/Qwen/Qwen3-8B . Immutable revision and downloaded file hashes are in `model.json` and `model_files.json`. Model licence: Apache 2.0; copy retained with the weights.
- Official CityU undergraduate catalogue 2026/27: https://www.cityu.edu.hk/catalogue/ug/202627/catalogue/B/B_course_CS.htm and https://www.cityu.edu.hk/catalogue/ug/202627/catalogue/B/B_ge_course_index.htm . Discovered course links are saved in `../data/catalogue_links.json`.
- Public syllabus PDFs linked by that catalogue: `https://www.cityu.edu.hk/ug/202627/course/COURSE_CODE.pdf`. Each normalized record contains its exact source URL, retrieval timestamp and SHA-256. Original PDFs and extracted text are under `../data/raw/syllabi/`. The effective term in a syllabus is not proof that it is offered in a particular semester.
- CityU robots policy: https://www.cityu.edu.hk/robots.txt . Snapshot saved as `cityu-robots.txt`. Some catalogue HTML responses were access challenges; that fetch was stopped. Publicly linked PDF downloads were available and fetched at two-second intervals. No portal access or authentication was attempted.
- Timetable access: https://www.cityu.edu.hk/arro/creg/schd_main.htm and https://www.cityu.edu.hk/sgs/student/masters/coursereg/guide . The Master Class Schedule is accessed through CityU Portal/AIMS. No live timetable, seat availability, or assessment-week schedule was obtained.
- Proposal reference https://github.com/wadefagen/datasets/ . GitHub licence endpoint returned HTTP 404 on the collection date (`4.txt`). This does not establish reuse permission. No rows from this repository were used for training or matching.
- Proposal reference https://github.com/ScottyLabs/cmucourses . GitHub licence endpoint returned HTTP 404 (`5.txt`). Software/data reuse permission and underlying evaluation access remain unverified. No rows were used for training or matching.

CityU materials are retained locally for the requested prototype. Public availability is not a blanket redistribution licence. Cross-university matching and evaluation transfer are deferred until authorized source data are available; external grades or evaluations must not be presented as CityU workload truth.
