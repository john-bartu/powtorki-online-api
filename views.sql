create definer = m1420_po_dev@`89.64.43.142` view v_page_character as
select `pt`.`name`         AS `type_name`,
       `p`.`id`            AS `id`,
       `p`.`id_author`     AS `id_author`,
       `p`.`id_type`       AS `id_type`,
       `p`.`title`         AS `title`,
       `p`.`document`      AS `document`,
       `p`.`description`   AS `description`,
       `p`.`time_creation` AS `time_creation`,
       `p`.`time_edited`   AS `time_edited`,
       `p`.`slug`          AS `slug`
from (`m1420_powtorki_dev`.`pages` `p`
         join `m1420_powtorki_dev`.`page_types` `pt` on ((`pt`.`id` = `p`.`id_type`)))
where (`p`.`id_type` = 4);


create definer = m1420_po_dev@`89.64.43.142` view v_page_date as
select `pt`.`name`         AS `type_name`,
       `p`.`id`            AS `id`,
       `p`.`id_author`     AS `id_author`,
       `p`.`id_type`       AS `id_type`,
       `p`.`title`         AS `title`,
       `p`.`document`      AS `document`,
       `p`.`description`   AS `description`,
       `p`.`time_creation` AS `time_creation`,
       `p`.`time_edited`   AS `time_edited`,
       `p`.`slug`          AS `slug`,
       `d`.`id_page`       AS `id_page`,
       `d`.`date_number`   AS `date_number`,
       `d`.`date_text`     AS `date_text`
from ((`m1420_powtorki_dev`.`pages` `p` join `m1420_powtorki_dev`.`page_types` `pt` on ((`pt`.`id` = `p`.`id_type`)))
         left join `m1420_powtorki_dev`.`dates` `d` on ((`p`.`id` = `d`.`id_page`)))
where (`p`.`id_type` = 5);

create definer = m1420_po_dev@`89.64.43.142` view v_page_dictionary as
select `pt`.`name`         AS `type_name`,
       `p`.`id`            AS `id`,
       `p`.`id_author`     AS `id_author`,
       `p`.`id_type`       AS `id_type`,
       `p`.`title`         AS `title`,
       `p`.`document`      AS `document`,
       `p`.`description`   AS `description`,
       `p`.`time_creation` AS `time_creation`,
       `p`.`time_edited`   AS `time_edited`,
       `p`.`slug`          AS `slug`
from (`m1420_powtorki_dev`.`pages` `p`
         join `m1420_powtorki_dev`.`page_types` `pt` on ((`pt`.`id` = `p`.`id_type`)))
where (`p`.`id_type` = 6);

create definer = m1420_po_dev@`89.64.43.142` view v_page_document as
select `pt`.`name`         AS `type_name`,
       `p`.`id`            AS `id`,
       `p`.`id_author`     AS `id_author`,
       `p`.`id_type`       AS `id_type`,
       `p`.`title`         AS `title`,
       `p`.`document`      AS `document`,
       `p`.`description`   AS `description`,
       `p`.`time_creation` AS `time_creation`,
       `p`.`time_edited`   AS `time_edited`,
       `p`.`slug`          AS `slug`
from (`m1420_powtorki_dev`.`pages` `p`
         join `m1420_powtorki_dev`.`page_types` `pt` on ((`pt`.`id` = `p`.`id_type`)))
where (`p`.`id_type` = 2);

create definer = m1420_po_dev@`89.64.43.142` view v_page_mindmap as
select `pt`.`name`         AS `type_name`,
       `p`.`id`            AS `id`,
       `p`.`id_author`     AS `id_author`,
       `p`.`id_type`       AS `id_type`,
       `p`.`title`         AS `title`,
       `p`.`document`      AS `document`,
       `p`.`description`   AS `description`,
       `p`.`time_creation` AS `time_creation`,
       `p`.`time_edited`   AS `time_edited`,
       `p`.`slug`          AS `slug`
from (`m1420_powtorki_dev`.`pages` `p`
         join `m1420_powtorki_dev`.`page_types` `pt` on ((`pt`.`id` = `p`.`id_type`)))
where (`p`.`id_type` = 9);

create definer = m1420_po_dev@`89.64.43.142` view v_page_questionanswer as
select `pt`.`name`         AS `type_name`,
       `p`.`id`            AS `id`,
       `p`.`id_author`     AS `id_author`,
       `p`.`id_type`       AS `id_type`,
       `p`.`title`         AS `title`,
       `p`.`document`      AS `document`,
       `p`.`description`   AS `description`,
       `p`.`time_creation` AS `time_creation`,
       `p`.`time_edited`   AS `time_edited`,
       `p`.`slug`          AS `slug`
from (`m1420_powtorki_dev`.`pages` `p`
         join `m1420_powtorki_dev`.`page_types` `pt` on ((`pt`.`id` = `p`.`id_type`)))
where (`p`.`id_type` = 7);

create definer = m1420_po_dev@`89.64.43.142` view v_page_quiz as
select `pt`.`name`         AS `type_name`,
       `p`.`id`            AS `id`,
       `p`.`id_author`     AS `id_author`,
       `p`.`id_type`       AS `id_type`,
       `p`.`title`         AS `title`,
       `p`.`document`      AS `document`,
       `p`.`description`   AS `description`,
       `p`.`time_creation` AS `time_creation`,
       `p`.`time_edited`   AS `time_edited`,
       `p`.`slug`          AS `slug`
from (`m1420_powtorki_dev`.`pages` `p`
         join `m1420_powtorki_dev`.`page_types` `pt` on ((`pt`.`id` = `p`.`id_type`)))
where (`p`.`id_type` = 8);

create definer = m1420_po_dev@`89.64.43.142` view v_page_quiz_answers as
select `m1420_powtorki_dev`.`map_question_answer`.`id`          AS `id`,
       `m1420_powtorki_dev`.`map_question_answer`.`id_question` AS `id_question`,
       `m1420_powtorki_dev`.`map_question_answer`.`id_answer`   AS `id_answer`,
       `m1420_powtorki_dev`.`map_question_answer`.`is_correct`  AS `is_correct`,
       `a`.`answer`                                             AS `answer`
from (`m1420_powtorki_dev`.`map_question_answer`
         join `m1420_powtorki_dev`.`answers` `a`
              on ((`m1420_powtorki_dev`.`map_question_answer`.`id_answer` = `a`.`id`)));

